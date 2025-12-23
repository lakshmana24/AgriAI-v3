from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    FARMER = "farmer"
    OFFICER = "officer"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = Field(default="bearer")
    role: UserRole
    expires_in: int


class UserPublic(BaseModel):
    username: str
    role: UserRole
