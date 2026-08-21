import base64
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import settings


ROLE_LEVELS = {"viewer": 10, "analyst": 20, "admin": 30}
_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    username: str
    role: str


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}")


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    if not password:
        raise ValueError("Password must not be empty")
    salt = salt or secrets.token_bytes(16)
    n, r, p = 16_384, 8, 1
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=n,
        r=r,
        p=p,
        dklen=32,
    )
    return f"scrypt${n}${r}${p}${_b64encode(salt)}${_b64encode(digest)}"


def verify_password(password: str, encoded_hash: str) -> bool:
    try:
        algorithm, raw_n, raw_r, raw_p, raw_salt, raw_digest = encoded_hash.split("$", 5)
        if algorithm != "scrypt":
            return False
        n, r, p = int(raw_n), int(raw_r), int(raw_p)
        salt = _b64decode(raw_salt)
        expected = _b64decode(raw_digest)
        actual = hashlib.scrypt(
            password.encode("utf-8"),
            salt=salt,
            n=n,
            r=r,
            p=p,
            dklen=len(expected),
        )
    except (ValueError, TypeError, base64.binascii.Error):
        return False
    return hmac.compare_digest(actual, expected)


def authenticate_configured_user(username: str, password: str) -> Principal | None:
    if not settings.auth_enabled:
        return None

    username_ok = hmac.compare_digest(username, settings.auth_username)
    password_ok = verify_password(password, settings.auth_password_hash)
    if not username_ok or not password_ok:
        return None
    return Principal(username=settings.auth_username, role=settings.auth_role)


def issue_access_token(principal: Principal) -> tuple[str, int]:
    now = int(time.time())
    expires_in = settings.auth_token_ttl_minutes * 60
    claims = {
        "sub": principal.username,
        "role": principal.role,
        "iat": now,
        "exp": now + expires_in,
        "jti": secrets.token_hex(12),
    }
    encoded_claims = _b64encode(
        json.dumps(claims, separators=(",", ":"), sort_keys=True).encode("utf-8")
    )
    signature = hmac.new(
        settings.auth_secret.encode("utf-8"),
        encoded_claims.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{encoded_claims}.{_b64encode(signature)}", expires_in


def decode_access_token(token: str) -> Principal:
    try:
        encoded_claims, encoded_signature = token.split(".", 1)
        expected_signature = hmac.new(
            settings.auth_secret.encode("utf-8"),
            encoded_claims.encode("ascii"),
            hashlib.sha256,
        ).digest()
        supplied_signature = _b64decode(encoded_signature)
        if not hmac.compare_digest(expected_signature, supplied_signature):
            raise ValueError("invalid signature")

        claims = json.loads(_b64decode(encoded_claims).decode("utf-8"))
        username = str(claims["sub"])
        role = str(claims["role"])
        expires_at = int(claims["exp"])
        if not username or role not in ROLE_LEVELS:
            raise ValueError("invalid claims")
        if expires_at <= int(time.time()):
            raise ValueError("expired")
    except (ValueError, KeyError, TypeError, json.JSONDecodeError, base64.binascii.Error) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return Principal(username=username, role=role)


async def get_current_principal(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Principal:
    if not settings.auth_enabled:
        return Principal(username="development", role="admin")

    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)


def require_role(minimum_role: str):
    if minimum_role not in ROLE_LEVELS:
        raise ValueError(f"Unknown role: {minimum_role}")

    async def dependency(
        principal: Annotated[Principal, Depends(get_current_principal)],
    ) -> Principal:
        if ROLE_LEVELS.get(principal.role, -1) < ROLE_LEVELS[minimum_role]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {minimum_role} or higher",
            )
        return principal

    return dependency
