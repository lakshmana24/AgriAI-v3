from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from jose import jwt
from passlib.context import CryptContext

from app.core.config import get_settings
from app.schemas.auth import UserPublic, UserRole

settings = get_settings()

_pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


@dataclass(frozen=True)
class AuthError(Exception):
    message: str


class AuthService:
    """Demo auth service.

    - Users are stored in-memory
    - Tokens are JWT (stateless)
    """

    def __init__(self) -> None:
        self._users: Dict[str, dict] = {
            "farmer01": {
                "username": "farmer01",
                "hashed_password": _pwd_context.hash("passfarm1"),
                "role": UserRole.FARMER,
            },
            "agrioff01": {
                "username": "agrioff01",
                "hashed_password": _pwd_context.hash("agripass@gov"),
                "role": UserRole.OFFICER,
            },
        }

    def authenticate(self, username: str, password: str) -> Optional[UserPublic]:
        user = self._users.get(username)
        if not user:
            return None
        if not _pwd_context.verify(password, user["hashed_password"]):
            return None
        return UserPublic(username=user["username"], role=user["role"])

    def create_access_token(self, user: UserPublic) -> str:
        if not settings.jwt_secret_key:
            raise AuthError("JWT_SECRET_KEY is not configured")

        now = datetime.now(timezone.utc)
        exp = now + timedelta(minutes=settings.jwt_access_token_expires_minutes)
        payload = {
            "sub": user.username,
            "role": user.role.value,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    def get_user(self, username: str) -> Optional[UserPublic]:
        user = self._users.get(username)
        if not user:
            return None
        return UserPublic(username=user["username"], role=user["role"])


auth_service = AuthService()
