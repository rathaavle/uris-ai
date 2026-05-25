"""
Authentication service for URIS-AI.

Handles JWT token creation, validation, and password hashing.
Supports Azure Active Directory integration and local JWT auth.

Requirements: 10.1, 10.2
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# Password hashing context.
# Use sha256_crypt as the primary scheme to avoid passlib/bcrypt compatibility
# issues on Python 3.12+.  bcrypt is kept as a deprecated fallback so that
# existing bcrypt hashes stored in the database can still be verified.
pwd_context = CryptContext(
    schemes=["sha256_crypt", "bcrypt"],
    deprecated=["bcrypt"],
    sha256_crypt__default_rounds=260000,
)


class AuthService:
    """
    Service for authentication and authorization operations.

    Handles:
    - Password hashing and verification
    - JWT token creation and decoding
    - Token expiration management

    Requirements: 10.1, 10.2
    """

    def __init__(
        self,
        secret_key: str,
        algorithm: str = "HS256",
        access_token_expire_minutes: int = 30,
    ):
        """
        Initialize the AuthService.

        Args:
            secret_key: Secret key for JWT signing
            algorithm: JWT signing algorithm (default: HS256)
            access_token_expire_minutes: Token expiration time in minutes
        """
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.access_token_expire_minutes = access_token_expire_minutes

    def hash_password(self, password: str) -> str:
        """
        Hash a plain-text password using bcrypt.

        Args:
            password: Plain-text password

        Returns:
            Bcrypt-hashed password string
        """
        return pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain-text password against a hashed password.

        Args:
            plain_password: Plain-text password to verify
            hashed_password: Stored bcrypt hash

        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)

    def create_access_token(
        self,
        subject: str,
        role: str,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a signed JWT access token.

        Args:
            subject: Token subject (typically username)
            role: User role to embed in the token
            expires_delta: Custom expiration delta (uses default if None)

        Returns:
            Encoded JWT token string
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=self.access_token_expire_minutes)

        expire = datetime.now(timezone.utc) + expires_delta

        payload = {
            "sub": subject,
            "role": role,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }

        token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
        # python-jose kadang return bytes, pastikan selalu str
        if isinstance(token, bytes):
            token = token.decode("utf-8")
        logger.debug(f"Access token created for subject '{subject}', role='{role}'")
        return token

    def decode_token(self, token: str) -> Optional[str]:
        """
        Decode a JWT token and return the subject (username).

        Args:
            token: JWT token string

        Returns:
            Username (subject) if token is valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: Optional[str] = payload.get("sub")
            return username
        except JWTError as exc:
            logger.warning(f"JWT decode error: {exc}")
            return None

    def get_token_role(self, token: str) -> Optional[str]:
        """
        Extract the role claim from a JWT token.

        Args:
            token: JWT token string

        Returns:
            Role string if token is valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload.get("role")
        except JWTError:
            return None
