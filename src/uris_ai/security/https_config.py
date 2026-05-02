"""
HTTPS/TLS configuration for URIS-AI.

Provides utilities for enforcing HTTPS connections and configuring
SSL/TLS certificates for secure communication.

Requirements: 10.5
"""

import logging
import ssl
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class HTTPSConfig:
    """
    Configuration for HTTPS/TLS enforcement.
    
    Provides methods to:
    - Create SSL context with proper TLS version
    - Load SSL certificates
    - Enforce HTTPS redirects
    
    Requirements: 10.5
    """

    # Minimum TLS version: TLS 1.2
    MIN_TLS_VERSION = ssl.TLSVersion.TLSv1_2

    def __init__(
        self,
        cert_file: Optional[str] = None,
        key_file: Optional[str] = None,
        ca_file: Optional[str] = None,
    ):
        """
        Initialize HTTPS configuration.
        
        Args:
            cert_file: Path to SSL certificate file
            key_file: Path to SSL private key file
            ca_file: Path to CA certificate file (optional)
        """
        self.cert_file = cert_file
        self.key_file = key_file
        self.ca_file = ca_file

    def create_ssl_context(self) -> ssl.SSLContext:
        """
        Create an SSL context with secure defaults.
        
        Enforces:
        - TLS 1.2 or higher
        - Strong cipher suites
        - Certificate verification
        
        Returns:
            Configured SSL context
            
        Requirements: 10.5
        """
        # Create SSL context with TLS 1.2+ only
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        
        # Set minimum TLS version to 1.2
        context.minimum_version = self.MIN_TLS_VERSION
        
        # Load certificate and private key if provided
        if self.cert_file and self.key_file:
            if not Path(self.cert_file).exists():
                raise FileNotFoundError(f"Certificate file not found: {self.cert_file}")
            if not Path(self.key_file).exists():
                raise FileNotFoundError(f"Key file not found: {self.key_file}")
            
            context.load_cert_chain(
                certfile=self.cert_file,
                keyfile=self.key_file,
            )
            logger.info(f"Loaded SSL certificate from {self.cert_file}")
        
        # Load CA certificate if provided
        if self.ca_file:
            if not Path(self.ca_file).exists():
                raise FileNotFoundError(f"CA file not found: {self.ca_file}")
            context.load_verify_locations(cafile=self.ca_file)
            logger.info(f"Loaded CA certificate from {self.ca_file}")
        
        # Set secure cipher suites (exclude weak ciphers)
        context.set_ciphers(
            "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"
        )
        
        # Enable certificate verification
        context.check_hostname = True
        context.verify_mode = ssl.CERT_REQUIRED
        
        logger.info("SSL context created with TLS 1.2+ enforcement")
        return context

    @staticmethod
    def get_uvicorn_ssl_config(
        cert_file: str,
        key_file: str,
    ) -> dict:
        """
        Get SSL configuration for Uvicorn server.
        
        Args:
            cert_file: Path to SSL certificate file
            key_file: Path to SSL private key file
            
        Returns:
            Dictionary with Uvicorn SSL configuration
            
        Requirements: 10.5
        """
        return {
            "ssl_certfile": cert_file,
            "ssl_keyfile": key_file,
            "ssl_version": ssl.PROTOCOL_TLS_SERVER,
            "ssl_cert_reqs": ssl.CERT_NONE,  # Client cert not required
            "ssl_ca_certs": None,
        }

    @staticmethod
    def validate_certificate(cert_file: str) -> bool:
        """
        Validate an SSL certificate file.
        
        Args:
            cert_file: Path to certificate file
            
        Returns:
            True if certificate is valid, False otherwise
        """
        try:
            import OpenSSL.crypto
            
            with open(cert_file, "r") as f:
                cert_data = f.read()
            
            cert = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, cert_data
            )
            
            # Check if certificate has expired
            if cert.has_expired():
                logger.error(f"Certificate has expired: {cert_file}")
                return False
            
            logger.info(f"Certificate is valid: {cert_file}")
            return True
            
        except Exception as exc:
            logger.error(f"Error validating certificate: {exc}", exc_info=True)
            return False

