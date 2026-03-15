"""Authentication routes."""

from __future__ import annotations

from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, HTTPException, Response

from app.api.dependencies import enforce_rate_limit, get_current_user
from app.config import get_settings
from app.core.auth import create_access_token, is_valid_credentials

settings = get_settings()
router = APIRouter()


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=1, max_length=256)


@router.post("/login")
async def login(payload: LoginRequest, response: Response, _: None = Depends(enforce_rate_limit)):
    if not is_valid_credentials(payload.username, payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token(subject=payload.username)
    response.set_cookie(
        key="obelisk_access_token",
        value=token,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        max_age=settings.access_token_expire_minutes * 60,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,
        "user": {"username": payload.username},
    }


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("obelisk_access_token")
    return {"status": "ok"}


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    return {"user": {"username": user.get("sub", "")}}
