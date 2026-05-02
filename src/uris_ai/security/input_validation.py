"""
Input validation and sanitization for URIS-AI.

Provides utilities to validate and sanitize user inputs to prevent
SQL injection, XSS, and other injection attacks.

Requirements: 10.4
"""

import html
import logging
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)


class InputValidator:
    """
    Validator for user inputs to prevent injection attacks.
    
    Provides methods to:
    - Validate input types and ranges
    - Sanitize strings to prevent XSS
    - Validate SQL-safe inputs
    - Validate geographic coordinates
    - Validate date/time inputs
    
    Requirements: 10.4
    """

    # Regex patterns for validation
    ALPHANUMERIC_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")
    EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    
    # Dangerous patterns that might indicate injection attempts
    SQL_INJECTION_PATTERNS = [
        re.compile(r"(\bOR\b|\bAND\b).*=.*", re.IGNORECASE),
        re.compile(r";\s*(DROP|DELETE|INSERT|UPDATE|ALTER|CREATE)\b", re.IGNORECASE),
        re.compile(r"--", re.IGNORECASE),
        re.compile(r"/\*.*\*/", re.IGNORECASE),
        re.compile(r"'\s*(OR|AND)\s*'", re.IGNORECASE),
        re.compile(r"UNION\s+SELECT", re.IGNORECASE),
    ]
    
    XSS_PATTERNS = [
        re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL),
        re.compile(r"javascript:", re.IGNORECASE),
        re.compile(r"on\w+\s*=", re.IGNORECASE),  # Event handlers like onclick=
        re.compile(r"<iframe", re.IGNORECASE),
        re.compile(r"<object", re.IGNORECASE),
        re.compile(r"<embed", re.IGNORECASE),
    ]

    @staticmethod
    def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize a string to prevent XSS attacks.
        
        - HTML-escapes special characters
        - Removes dangerous patterns
        - Truncates to max length if specified
        
        Args:
            value: Input string to sanitize
            max_length: Maximum allowed length (optional)
            
        Returns:
            Sanitized string
            
        Requirements: 10.4
        """
        if not isinstance(value, str):
            raise ValueError("Input must be a string")
        
        # HTML escape to prevent XSS
        sanitized = html.escape(value, quote=True)
        
        # Remove null bytes
        sanitized = sanitized.replace("\x00", "")
        
        # Truncate if max_length specified
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length]
            logger.warning(f"Input truncated to {max_length} characters")
        
        return sanitized

    @classmethod
    def validate_no_sql_injection(cls, value: str) -> bool:
        """
        Check if input contains SQL injection patterns.
        
        Args:
            value: Input string to validate
            
        Returns:
            True if safe, False if suspicious patterns detected
            
        Requirements: 10.4
        """
        for pattern in cls.SQL_INJECTION_PATTERNS:
            if pattern.search(value):
                logger.warning(f"Potential SQL injection detected: {value[:50]}")
                return False
        return True

    @classmethod
    def validate_no_xss(cls, value: str) -> bool:
        """
        Check if input contains XSS patterns.
        
        Args:
            value: Input string to validate
            
        Returns:
            True if safe, False if suspicious patterns detected
            
        Requirements: 10.4
        """
        for pattern in cls.XSS_PATTERNS:
            if pattern.search(value):
                logger.warning(f"Potential XSS detected: {value[:50]}")
                return False
        return True

    @staticmethod
    def validate_integer(
        value: Any,
        min_value: Optional[int] = None,
        max_value: Optional[int] = None,
    ) -> int:
        """
        Validate and convert input to integer with range checking.
        
        Args:
            value: Input value to validate
            min_value: Minimum allowed value (optional)
            max_value: Maximum allowed value (optional)
            
        Returns:
            Validated integer
            
        Raises:
            ValueError: If validation fails
            
        Requirements: 10.4
        """
        try:
            int_value = int(value)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid integer: {value}") from exc
        
        if min_value is not None and int_value < min_value:
            raise ValueError(f"Value {int_value} is below minimum {min_value}")
        
        if max_value is not None and int_value > max_value:
            raise ValueError(f"Value {int_value} exceeds maximum {max_value}")
        
        return int_value

    @staticmethod
    def validate_float(
        value: Any,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
    ) -> float:
        """
        Validate and convert input to float with range checking.
        
        Args:
            value: Input value to validate
            min_value: Minimum allowed value (optional)
            max_value: Maximum allowed value (optional)
            
        Returns:
            Validated float
            
        Raises:
            ValueError: If validation fails
            
        Requirements: 10.4
        """
        try:
            float_value = float(value)
        except (ValueError, TypeError) as exc:
            raise ValueError(f"Invalid float: {value}") from exc
        
        if min_value is not None and float_value < min_value:
            raise ValueError(f"Value {float_value} is below minimum {min_value}")
        
        if max_value is not None and float_value > max_value:
            raise ValueError(f"Value {float_value} exceeds maximum {max_value}")
        
        return float_value

    @staticmethod
    def validate_region_id(region_id: Any) -> int:
        """
        Validate region ID.
        
        Args:
            region_id: Region ID to validate
            
        Returns:
            Validated region ID
            
        Raises:
            ValueError: If validation fails
            
        Requirements: 10.4
        """
        return InputValidator.validate_integer(region_id, min_value=1)

    @staticmethod
    def validate_latitude(latitude: Any) -> float:
        """
        Validate latitude coordinate.
        
        Args:
            latitude: Latitude value to validate
            
        Returns:
            Validated latitude
            
        Raises:
            ValueError: If validation fails
            
        Requirements: 10.4
        """
        return InputValidator.validate_float(latitude, min_value=-90.0, max_value=90.0)

    @staticmethod
    def validate_longitude(longitude: Any) -> float:
        """
        Validate longitude coordinate.
        
        Args:
            longitude: Longitude value to validate
            
        Returns:
            Validated longitude
            
        Raises:
            ValueError: If validation fails
            
        Requirements: 10.4
        """
        return InputValidator.validate_float(longitude, min_value=-180.0, max_value=180.0)

    @classmethod
    def validate_alphanumeric(cls, value: str, max_length: int = 255) -> str:
        """
        Validate that string contains only alphanumeric characters, hyphens, and underscores.
        
        Args:
            value: String to validate
            max_length: Maximum allowed length
            
        Returns:
            Validated string
            
        Raises:
            ValueError: If validation fails
            
        Requirements: 10.4
        """
        if not isinstance(value, str):
            raise ValueError("Input must be a string")
        
        if len(value) > max_length:
            raise ValueError(f"String exceeds maximum length of {max_length}")
        
        if not cls.ALPHANUMERIC_PATTERN.match(value):
            raise ValueError("String contains invalid characters")
        
        return value

    @classmethod
    def validate_email(cls, email: str) -> str:
        """
        Validate email address format.
        
        Args:
            email: Email address to validate
            
        Returns:
            Validated email
            
        Raises:
            ValueError: If validation fails
            
        Requirements: 10.4
        """
        if not isinstance(email, str):
            raise ValueError("Email must be a string")
        
        if not cls.EMAIL_PATTERN.match(email):
            raise ValueError("Invalid email format")
        
        return email.lower()

    @staticmethod
    def validate_risk_score(score: Any) -> float:
        """
        Validate risk score (0-100).
        
        Args:
            score: Risk score to validate
            
        Returns:
            Validated risk score
            
        Raises:
            ValueError: If validation fails
            
        Requirements: 10.4
        """
        return InputValidator.validate_float(score, min_value=0.0, max_value=100.0)

    @staticmethod
    def validate_and_sanitize_text(
        text: str,
        max_length: int = 1000,
        allow_html: bool = False,
    ) -> str:
        """
        Validate and sanitize text input.
        
        Args:
            text: Text to validate and sanitize
            max_length: Maximum allowed length
            allow_html: Whether to allow HTML (default: False)
            
        Returns:
            Validated and sanitized text
            
        Raises:
            ValueError: If validation fails
            
        Requirements: 10.4
        """
        if not isinstance(text, str):
            raise ValueError("Input must be a string")
        
        # Check for SQL injection patterns
        if not InputValidator.validate_no_sql_injection(text):
            raise ValueError("Input contains suspicious SQL patterns")
        
        # Check for XSS patterns if HTML not allowed
        if not allow_html and not InputValidator.validate_no_xss(text):
            raise ValueError("Input contains suspicious XSS patterns")
        
        # Sanitize
        sanitized = InputValidator.sanitize_string(text, max_length=max_length)
        
        return sanitized

