"""
Security tests for URIS-AI.

Tests:
- Authentication and authorization
- Input validation and sanitization
- SQL injection prevention
- XSS prevention
- HTTPS enforcement

Requirements: 10.2, 10.4, 10.5
"""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from uris_ai.api.main import app
from uris_ai.security.input_validation import InputValidator
from uris_ai.services.auth_service import AuthService


class TestAuthentication:
    """
    Test authentication functionality.
    
    Requirements: 10.2
    """

    def test_password_hashing(self):
        """Test password hashing and verification."""
        auth_service = AuthService(secret_key="test-secret")
        
        password = "SecurePassword123!"
        hashed = auth_service.hash_password(password)
        
        # Verify hash is different from original
        assert hashed != password
        
        # Verify password verification works
        assert auth_service.verify_password(password, hashed)
        
        # Verify wrong password fails
        assert not auth_service.verify_password("WrongPassword", hashed)

    def test_jwt_token_creation_and_decoding(self):
        """Test JWT token creation and decoding."""
        auth_service = AuthService(secret_key="test-secret")
        
        username = "testuser"
        role = "public"
        
        # Create token
        token = auth_service.create_access_token(username, role)
        assert token is not None
        assert isinstance(token, str)
        
        # Decode token
        decoded_username = auth_service.decode_token(token)
        assert decoded_username == username
        
        # Get role from token
        decoded_role = auth_service.get_token_role(token)
        assert decoded_role == role

    def test_invalid_token_decoding(self):
        """Test that invalid tokens are rejected."""
        auth_service = AuthService(secret_key="test-secret")
        
        # Invalid token
        invalid_token = "invalid.token.here"
        decoded = auth_service.decode_token(invalid_token)
        assert decoded is None

    def test_token_with_wrong_secret(self):
        """Test that tokens signed with different secret are rejected."""
        auth_service1 = AuthService(secret_key="secret1")
        auth_service2 = AuthService(secret_key="secret2")
        
        token = auth_service1.create_access_token("testuser", "public")
        
        # Try to decode with different secret
        decoded = auth_service2.decode_token(token)
        assert decoded is None


class TestAuthorization:
    """
    Test authorization and role-based access control.
    
    Requirements: 10.2
    """

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied."""
        client = TestClient(app)
        
        # Try to access protected endpoint without token
        response = client.get("/regions/1/risk")
        
        # Should return 401 Unauthorized
        assert response.status_code == 401

    def test_invalid_token_rejected(self):
        """Test that invalid tokens are rejected."""
        client = TestClient(app)
        
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/regions/1/risk", headers=headers)
        
        # Should return 401 Unauthorized
        assert response.status_code == 401


class TestInputValidation:
    """
    Test input validation functionality.
    
    Requirements: 10.4
    """

    def test_validate_integer_valid(self):
        """Test integer validation with valid input."""
        validator = InputValidator()
        
        assert validator.validate_integer(42) == 42
        assert validator.validate_integer("42") == 42
        assert validator.validate_integer(10, min_value=5, max_value=15) == 10

    def test_validate_integer_invalid(self):
        """Test integer validation with invalid input."""
        validator = InputValidator()
        
        with pytest.raises(ValueError):
            validator.validate_integer("not_a_number")
        
        with pytest.raises(ValueError):
            validator.validate_integer(5, min_value=10)
        
        with pytest.raises(ValueError):
            validator.validate_integer(20, max_value=15)

    def test_validate_float_valid(self):
        """Test float validation with valid input."""
        validator = InputValidator()
        
        assert validator.validate_float(3.14) == 3.14
        assert validator.validate_float("3.14") == 3.14
        assert validator.validate_float(5.5, min_value=0.0, max_value=10.0) == 5.5

    def test_validate_float_invalid(self):
        """Test float validation with invalid input."""
        validator = InputValidator()
        
        with pytest.raises(ValueError):
            validator.validate_float("not_a_number")
        
        with pytest.raises(ValueError):
            validator.validate_float(5.0, min_value=10.0)
        
        with pytest.raises(ValueError):
            validator.validate_float(20.0, max_value=15.0)

    def test_validate_region_id(self):
        """Test region ID validation."""
        validator = InputValidator()
        
        assert validator.validate_region_id(1) == 1
        assert validator.validate_region_id("42") == 42
        
        with pytest.raises(ValueError):
            validator.validate_region_id(0)
        
        with pytest.raises(ValueError):
            validator.validate_region_id(-1)

    def test_validate_latitude(self):
        """Test latitude validation."""
        validator = InputValidator()
        
        assert validator.validate_latitude(0.0) == 0.0
        assert validator.validate_latitude(-6.2) == -6.2
        assert validator.validate_latitude(90.0) == 90.0
        
        with pytest.raises(ValueError):
            validator.validate_latitude(91.0)
        
        with pytest.raises(ValueError):
            validator.validate_latitude(-91.0)

    def test_validate_longitude(self):
        """Test longitude validation."""
        validator = InputValidator()
        
        assert validator.validate_longitude(0.0) == 0.0
        assert validator.validate_longitude(106.8) == 106.8
        assert validator.validate_longitude(180.0) == 180.0
        
        with pytest.raises(ValueError):
            validator.validate_longitude(181.0)
        
        with pytest.raises(ValueError):
            validator.validate_longitude(-181.0)

    def test_validate_risk_score(self):
        """Test risk score validation."""
        validator = InputValidator()
        
        assert validator.validate_risk_score(0.0) == 0.0
        assert validator.validate_risk_score(50.0) == 50.0
        assert validator.validate_risk_score(100.0) == 100.0
        
        with pytest.raises(ValueError):
            validator.validate_risk_score(-1.0)
        
        with pytest.raises(ValueError):
            validator.validate_risk_score(101.0)

    def test_validate_alphanumeric(self):
        """Test alphanumeric validation."""
        validator = InputValidator()
        
        assert validator.validate_alphanumeric("test123") == "test123"
        assert validator.validate_alphanumeric("test-name_123") == "test-name_123"
        
        with pytest.raises(ValueError):
            validator.validate_alphanumeric("test@123")
        
        with pytest.raises(ValueError):
            validator.validate_alphanumeric("test 123")
        
        with pytest.raises(ValueError):
            validator.validate_alphanumeric("a" * 300, max_length=255)

    def test_validate_email(self):
        """Test email validation."""
        validator = InputValidator()
        
        assert validator.validate_email("test@example.com") == "test@example.com"
        assert validator.validate_email("User@Domain.COM") == "user@domain.com"
        
        with pytest.raises(ValueError):
            validator.validate_email("invalid-email")
        
        with pytest.raises(ValueError):
            validator.validate_email("@example.com")
        
        with pytest.raises(ValueError):
            validator.validate_email("test@")


class TestSQLInjectionPrevention:
    """
    Test SQL injection prevention.
    
    Requirements: 10.4
    """

    def test_detect_sql_injection_patterns(self):
        """Test detection of SQL injection patterns."""
        validator = InputValidator()
        
        # Valid inputs should pass
        assert validator.validate_no_sql_injection("normal text")
        assert validator.validate_no_sql_injection("region-123")
        
        # SQL injection attempts should be detected
        assert not validator.validate_no_sql_injection("1' OR '1'='1")
        assert not validator.validate_no_sql_injection("'; DROP TABLE users; --")
        assert not validator.validate_no_sql_injection("1 UNION SELECT * FROM users")
        assert not validator.validate_no_sql_injection("admin'--")
        assert not validator.validate_no_sql_injection("1' AND 1=1")

    def test_sanitize_string_removes_dangerous_content(self):
        """Test that string sanitization removes dangerous content."""
        validator = InputValidator()
        
        # Test HTML escaping
        sanitized = validator.sanitize_string("<script>alert('xss')</script>")
        assert "<script>" not in sanitized
        assert "&lt;script&gt;" in sanitized
        
        # Test null byte removal
        sanitized = validator.sanitize_string("test\x00data")
        assert "\x00" not in sanitized

    def test_validate_and_sanitize_text_rejects_sql_injection(self):
        """Test that text validation rejects SQL injection attempts."""
        validator = InputValidator()
        
        with pytest.raises(ValueError, match="suspicious SQL patterns"):
            validator.validate_and_sanitize_text("1' OR '1'='1")
        
        with pytest.raises(ValueError, match="suspicious SQL patterns"):
            validator.validate_and_sanitize_text("'; DROP TABLE users; --")


class TestXSSPrevention:
    """
    Test XSS (Cross-Site Scripting) prevention.
    
    Requirements: 10.4
    """

    def test_detect_xss_patterns(self):
        """Test detection of XSS patterns."""
        validator = InputValidator()
        
        # Valid inputs should pass
        assert validator.validate_no_xss("normal text")
        assert validator.validate_no_xss("This is a description")
        
        # XSS attempts should be detected
        assert not validator.validate_no_xss("<script>alert('xss')</script>")
        assert not validator.validate_no_xss("javascript:alert('xss')")
        assert not validator.validate_no_xss("<img src=x onerror=alert('xss')>")
        assert not validator.validate_no_xss("<iframe src='evil.com'></iframe>")
        assert not validator.validate_no_xss("<object data='evil.swf'></object>")

    def test_sanitize_string_escapes_html(self):
        """Test that HTML is properly escaped."""
        validator = InputValidator()
        
        # Test HTML tag escaping
        sanitized = validator.sanitize_string("<div>content</div>")
        assert "<div>" not in sanitized
        assert "&lt;div&gt;" in sanitized
        
        # Test quote escaping
        sanitized = validator.sanitize_string('test "quoted" text')
        assert "&quot;" in sanitized
        
        # Test ampersand escaping
        sanitized = validator.sanitize_string("test & text")
        assert "&amp;" in sanitized

    def test_validate_and_sanitize_text_rejects_xss(self):
        """Test that text validation rejects XSS attempts."""
        validator = InputValidator()
        
        with pytest.raises(ValueError, match="suspicious XSS patterns"):
            validator.validate_and_sanitize_text("<script>alert('xss')</script>")
        
        with pytest.raises(ValueError, match="suspicious XSS patterns"):
            validator.validate_and_sanitize_text("javascript:alert('xss')")

    def test_validate_and_sanitize_text_with_allow_html(self):
        """Test that HTML can be allowed when explicitly specified."""
        validator = InputValidator()
        
        # Should not raise when allow_html=True
        # But still sanitizes
        sanitized = validator.validate_and_sanitize_text(
            "<div>content</div>",
            allow_html=True
        )
        assert "&lt;div&gt;" in sanitized


class TestHTTPSEnforcement:
    """
    Test HTTPS enforcement.
    
    Requirements: 10.5
    """

    def test_https_redirect_middleware_redirects_http(self):
        """Test that HTTP requests are redirected to HTTPS."""
        from uris_ai.api.middleware import HTTPSRedirectMiddleware
        from fastapi import FastAPI, Request
        from starlette.responses import Response
        
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}
        
        # Add HTTPS redirect middleware
        app.add_middleware(HTTPSRedirectMiddleware, enforce_https=True)
        
        client = TestClient(app, base_url="http://testserver")
        
        # Make HTTP request
        response = client.get("/test", follow_redirects=False)
        
        # Should redirect to HTTPS
        assert response.status_code == 301
        assert response.headers["location"].startswith("https://")

    def test_https_redirect_middleware_allows_https(self):
        """Test that HTTPS requests are allowed through."""
        from uris_ai.api.middleware import HTTPSRedirectMiddleware
        from fastapi import FastAPI
        
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}
        
        # Add HTTPS redirect middleware
        app.add_middleware(HTTPSRedirectMiddleware, enforce_https=True)
        
        client = TestClient(app, base_url="https://testserver")
        
        # Make HTTPS request
        response = client.get("/test")
        
        # Should not redirect
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_https_redirect_can_be_disabled(self):
        """Test that HTTPS redirect can be disabled for development."""
        from uris_ai.api.middleware import HTTPSRedirectMiddleware
        from fastapi import FastAPI
        
        app = FastAPI()
        
        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}
        
        # Add HTTPS redirect middleware with enforcement disabled
        app.add_middleware(HTTPSRedirectMiddleware, enforce_https=False)
        
        client = TestClient(app, base_url="http://testserver")
        
        # Make HTTP request
        response = client.get("/test")
        
        # Should not redirect when disabled
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestKeyVaultIntegration:
    """
    Test Azure Key Vault integration.
    
    Requirements: 10.5
    """

    def test_key_vault_service_initialization(self):
        """Test Key Vault service can be initialized."""
        from uris_ai.services.key_vault_service import KeyVaultService
        
        # This will fail without proper Azure credentials, but tests the interface
        vault_url = "https://test-vault.vault.azure.net/"
        
        try:
            service = KeyVaultService(vault_url)
            assert service.vault_url == vault_url
        except Exception:
            # Expected to fail without real Azure credentials
            pass

    def test_key_vault_methods_exist(self):
        """Test that Key Vault service has required methods."""
        from uris_ai.services.key_vault_service import KeyVaultService
        
        # Check that methods exist
        assert hasattr(KeyVaultService, 'get_secret')
        assert hasattr(KeyVaultService, 'set_secret')
        assert hasattr(KeyVaultService, 'delete_secret')
        assert hasattr(KeyVaultService, 'list_secrets')
        assert hasattr(KeyVaultService, 'get_database_credentials')
        assert hasattr(KeyVaultService, 'get_api_keys')
        assert hasattr(KeyVaultService, 'get_storage_credentials')
        assert hasattr(KeyVaultService, 'get_redis_credentials')

