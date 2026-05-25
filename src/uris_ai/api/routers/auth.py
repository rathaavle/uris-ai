"""
Authentication router for URIS-AI API.

Handles user login, logout, and token management.
Integrates with Azure Active Directory via JWT.

Requirements: 10.1, 10.2
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from uris_ai.api.dependencies import get_auth_service, get_current_active_user, get_db
from uris_ai.api.schemas import LogoutResponse, TokenResponse
from uris_ai.models.database import User
from uris_ai.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login pengguna",
    description="Autentikasi pengguna dan kembalikan JWT access token.",
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """
    Authenticate a user and return a JWT access token.
    Supports OAuth2 form-data (untuk Swagger UI Authorize button).
    Requirements: 10.2
    """
    username = form_data.username
    password = form_data.password

    user = db.query(User).filter(User.username == username).first()

    if user is None or not auth_service.verify_password(password, user.password_hash):
        logger.warning(f"Failed login attempt for username '{username}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akun pengguna tidak aktif",
        )

    token = auth_service.create_access_token(
        subject=user.username,
        role=user.role,
    )

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    logger.info(f"User '{user.username}' logged in successfully (role={user.role})")

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=auth_service.access_token_expire_minutes * 60,
        role=user.role,
    )


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout pengguna",
    description="Logout pengguna saat ini. Token harus di-invalidate di sisi klien.",
)
async def logout(
    current_user: User = Depends(get_current_active_user),
) -> LogoutResponse:
    """
    Logout the current user.

    Since JWT tokens are stateless, actual invalidation must be handled
    client-side by discarding the token. This endpoint provides a
    consistent API surface for logout operations.

    Requirements: 10.2
    """
    logger.info(f"User '{current_user.username}' logged out")
    return LogoutResponse(message="Berhasil logout")
