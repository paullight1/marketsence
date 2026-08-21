from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.security import (
    Principal,
    authenticate_configured_user,
    get_current_principal,
    issue_access_token,
)


router = APIRouter()


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=1, max_length=1024)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    expires_in: int


class PrincipalResponse(BaseModel):
    username: str
    role: str


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    if not settings.auth_enabled:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Authentication is disabled for this environment",
        )

    principal = authenticate_configured_user(payload.username, payload.password)
    if principal is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token, expires_in = issue_access_token(principal)
    return TokenResponse(
        access_token=token,
        role=principal.role,
        expires_in=expires_in,
    )


@router.get("/me", response_model=PrincipalResponse)
async def me(
    principal: Annotated[Principal, Depends(get_current_principal)],
):
    return PrincipalResponse(username=principal.username, role=principal.role)
