import asyncio
import time
from dataclasses import dataclass

from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import settings


@dataclass(frozen=True)
class RateLimitDecision:
    allowed: bool
    limit: int
    remaining: int
    reset_after: int


class MemoryRateLimiter:
    def __init__(self) -> None:
        self._counts: dict[tuple[str, int], int] = {}
        self._lock = asyncio.Lock()

    async def ready(self) -> None:
        return None

    async def close(self) -> None:
        self._counts.clear()

    async def hit(self, key: str, limit: int, window_seconds: int = 60) -> RateLimitDecision:
        now = int(time.time())
        bucket = now // window_seconds
        reset_after = window_seconds - (now % window_seconds)
        async with self._lock:
            count_key = (key, bucket)
            current = self._counts.get(count_key, 0) + 1
            self._counts[count_key] = current
            if len(self._counts) > 10_000:
                minimum_bucket = bucket - 2
                self._counts = {
                    item_key: value
                    for item_key, value in self._counts.items()
                    if item_key[1] >= minimum_bucket
                }
        return RateLimitDecision(
            allowed=current <= limit,
            limit=limit,
            remaining=max(limit - current, 0),
            reset_after=max(reset_after, 1),
        )


class RedisRateLimiter:
    _SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('TTL', KEYS[1])
return {current, ttl}
"""

    def __init__(self, url: str) -> None:
        self._redis = Redis.from_url(url, encoding="utf-8", decode_responses=True)

    async def ready(self) -> None:
        await self._redis.ping()

    async def close(self) -> None:
        await self._redis.aclose()

    async def hit(self, key: str, limit: int, window_seconds: int = 60) -> RateLimitDecision:
        bucket = int(time.time()) // window_seconds
        redis_key = f"{key}:{bucket}"
        current, ttl = await self._redis.eval(
            self._SCRIPT,
            1,
            redis_key,
            window_seconds,
        )
        current = int(current)
        ttl = max(int(ttl), 1)
        return RateLimitDecision(
            allowed=current <= limit,
            limit=limit,
            remaining=max(limit - current, 0),
            reset_after=ttl,
        )


def build_rate_limiter():
    if settings.redis_url:
        return RedisRateLimiter(settings.redis_url)
    return MemoryRateLimiter()


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if (
            not settings.rate_limit_enabled
            or request.method == "OPTIONS"
            or request.url.path in {"/", "/health"}
        ):
            return await call_next(request)

        path = request.url.path
        if path == "/api/auth/login":
            category = "login"
            limit = settings.auth_login_limit_per_minute
        elif request.method in {"GET", "HEAD"}:
            category = "read"
            limit = settings.read_limit_per_minute
        else:
            category = "write"
            limit = settings.write_limit_per_minute

        client_host = request.client.host if request.client else "unknown"
        key = f"marketsense:rate:{settings.environment}:{category}:{client_host}"
        limiter = request.app.state.rate_limiter

        try:
            decision = await limiter.hit(key, limit, 60)
        except Exception:
            if settings.environment == "production":
                return JSONResponse(
                    status_code=503,
                    content={"detail": "Distributed rate limiter unavailable"},
                )
            return await call_next(request)

        headers = {
            "X-RateLimit-Limit": str(decision.limit),
            "X-RateLimit-Remaining": str(decision.remaining),
            "X-RateLimit-Reset": str(int(time.time()) + decision.reset_after),
        }
        if not decision.allowed:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={**headers, "Retry-After": str(decision.reset_after)},
            )

        response = await call_next(request)
        for header, value in headers.items():
            response.headers[header] = value
        return response
