"""
Users router for URIS-AI API.

Provides endpoints for user profile management.

Requirements: 10.2
"""

import logging

from fastapi import APIRouter, Depends

from uris_ai.api.dependencies import get_current_active_user
from uris_ai.api.schemas import UserResponse
from uris_ai.models.database import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Informasi pengguna saat ini",
    description="Kembalikan informasi profil pengguna yang sedang login.",
)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """
    Return profile information for the currently authenticated user.

    Requirements: 10.2
    """
    logger.debug(f"User info requested for '{current_user.username}'")
    return UserResponse.model_validate(current_user)
