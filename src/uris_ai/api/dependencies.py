"""
FastAPI dependency injection utilities for URIS-AI.

Provides reusable dependencies for database sessions, authentication,
and service instances.
"""

from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from uris_ai.config import settings
from uris_ai.models.database import User
from uris_ai.models.db_utils import create_db_engine, create_session_factory
from uris_ai.services.auth_service import AuthService
from uris_ai.security.input_validation import InputValidator

# HTTPBearer scheme — Swagger akan tampilkan input "Value" untuk paste token langsung
oauth2_scheme = HTTPBearer(auto_error=False)

# Database engine and session factory (initialized lazily)
_engine = None
_session_factory = None


def get_engine():
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        _engine = create_db_engine(settings.azure_mysql_connection_string)
    return _engine


def get_session_factory():
    """Get or create the session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = create_session_factory(get_engine())
    return _session_factory


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.

    Yields a session and ensures it is closed after the request.
    """
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_auth_service() -> AuthService:
    """Dependency that provides an AuthService instance."""
    return AuthService(
        secret_key=settings.secret_key,
        algorithm=settings.algorithm,
        access_token_expire_minutes=settings.access_token_expire_minutes,
    )


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """
    Dependency that extracts and validates the current authenticated user.
    Raises HTTP 401 if the token is missing or invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Tidak dapat memvalidasi kredensial",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if credentials is None:
        raise credentials_exception

    token = credentials.credentials
    username = auth_service.decode_token(token)
    if username is None:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None or not user.is_active:
        raise credentials_exception

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Dependency that ensures the current user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Pengguna tidak aktif",
        )
    return current_user


def require_role(*roles: str):
    """
    Dependency factory that enforces role-based access control.

    Usage:
        @router.get("/admin", dependencies=[Depends(require_role("government"))])
    """

    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Akses tidak diizinkan untuk peran Anda",
            )
        return current_user

    return role_checker


def get_input_validator() -> InputValidator:
    """
    Dependency that provides an InputValidator instance.
    
    Requirements: 10.4
    """
    return InputValidator()
