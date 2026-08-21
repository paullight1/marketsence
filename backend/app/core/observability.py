import json
import logging
import re
import time
import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


_request_id: ContextVar[str | None] = ContextVar("marketsense_request_id", default=None)
_request_logger = logging.getLogger("marketsense.request")
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._:-]{1,64}$")


def current_request_id() -> str | None:
    return _request_id.get()


def normalize_request_id(value: str | None) -> str:
    if value and _VALID_REQUEST_ID.fullmatch(value):
        return value
    return str(uuid.uuid4())


class ObservabilityMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = normalize_request_id(request.headers.get("X-Request-ID"))
        token = _request_id.set(request_id)
        request.state.request_id = request_id
        started = time.perf_counter()
        status_code = 500

        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 3)
            _request_logger.info(
                json.dumps(
                    {
                        "event": "http_request",
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "status": status_code,
                        "duration_ms": duration_ms,
                    },
                    separators=(",", ":"),
                    sort_keys=True,
                )
            )
            _request_id.reset(token)
