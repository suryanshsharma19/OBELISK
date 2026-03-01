"""Pydantic models for user data (placeholder for future auth)."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    is_active: bool = True


class UserCreate(UserBase):
    """Registration payload."""
    password: str = Field(..., min_length=8, max_length=128)


class UserResponse(UserBase):
    id: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
