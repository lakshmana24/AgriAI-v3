from __future__ import annotations

from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.core.config import get_settings
from app.schemas.auth import UserPublic, UserRole
from app.services.auth_service import auth_service

settings = get_settings()

_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(token: str = Depends(_oauth2_scheme)) -> UserPublic:
    if not settings.jwt_secret_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server auth is not configured.",
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        username = payload.get("sub")
        role = payload.get("role")
        if not username or not role:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = auth_service.get_user(username)
    if not user:
        raise credentials_exception
    return user


def require_role(required: UserRole) -> Callable[[UserPublic], UserPublic]:
    def _guard(user: UserPublic = Depends(get_current_user)) -> UserPublic:
        if user.role != required:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return user

    return _guard
