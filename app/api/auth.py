from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.schemas.auth import TokenResponse
from app.services.auth_service import AuthError, auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> TokenResponse:
    user = auth_service.authenticate(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token = auth_service.create_access_token(user)
    except AuthError as exc:
        raise HTTPException(status_code=500, detail=exc.message)

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        role=user.role,
        expires_in=settings.jwt_access_token_expires_minutes * 60  # Convert to seconds
    )
