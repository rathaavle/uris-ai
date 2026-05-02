"""
Azure Key Vault service for secrets management.

Provides secure storage and retrieval of sensitive configuration values
such as database credentials, API keys, and certificates.

Requirements: 10.5
"""

import logging
from typing import Optional

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.keyvault.secrets import SecretClient

logger = logging.getLogger(__name__)


class KeyVaultService:
    """
    Service for managing secrets in Azure Key Vault.
    
    Provides methods to:
    - Retrieve secrets from Key Vault
    - Set secrets in Key Vault
    - Delete secrets from Key Vault
    - List all secrets
    
    Requirements: 10.5
    """

    def __init__(self, vault_url: str):
        """
        Initialize the Key Vault service.
        
        Args:
            vault_url: Azure Key Vault URL (e.g., https://my-vault.vault.azure.net/)
        """
        self.vault_url = vault_url
        self.credential = DefaultAzureCredential()
        self.client = SecretClient(vault_url=vault_url, credential=self.credential)
        logger.info(f"Key Vault service initialized for vault: {vault_url}")

    def get_secret(self, secret_name: str) -> Optional[str]:
        """
        Retrieve a secret from Key Vault.
        
        Args:
            secret_name: Name of the secret to retrieve
            
        Returns:
            Secret value if found, None otherwise
        """
        try:
            secret = self.client.get_secret(secret_name)
            logger.debug(f"Retrieved secret: {secret_name}")
            return secret.value
        except ResourceNotFoundError:
            logger.warning(f"Secret not found: {secret_name}")
            return None
        except Exception as exc:
            logger.error(f"Error retrieving secret {secret_name}: {exc}", exc_info=True)
            return None

    def set_secret(self, secret_name: str, secret_value: str) -> bool:
        """
        Store a secret in Key Vault.
        
        Args:
            secret_name: Name of the secret
            secret_value: Value to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.set_secret(secret_name, secret_value)
            logger.info(f"Secret stored: {secret_name}")
            return True
        except Exception as exc:
            logger.error(f"Error storing secret {secret_name}: {exc}", exc_info=True)
            return False

    def delete_secret(self, secret_name: str) -> bool:
        """
        Delete a secret from Key Vault.
        
        Args:
            secret_name: Name of the secret to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            poller = self.client.begin_delete_secret(secret_name)
            poller.wait()
            logger.info(f"Secret deleted: {secret_name}")
            return True
        except ResourceNotFoundError:
            logger.warning(f"Secret not found for deletion: {secret_name}")
            return False
        except Exception as exc:
            logger.error(f"Error deleting secret {secret_name}: {exc}", exc_info=True)
            return False

    def list_secrets(self) -> list[str]:
        """
        List all secret names in the Key Vault.
        
        Returns:
            List of secret names
        """
        try:
            secret_properties = self.client.list_properties_of_secrets()
            secret_names = [prop.name for prop in secret_properties]
            logger.debug(f"Listed {len(secret_names)} secrets")
            return secret_names
        except Exception as exc:
            logger.error(f"Error listing secrets: {exc}", exc_info=True)
            return []

    def get_database_credentials(self) -> dict[str, Optional[str]]:
        """
        Retrieve database credentials from Key Vault.
        
        Returns:
            Dictionary with database connection details
        """
        return {
            "server": self.get_secret("azure-sql-server"),
            "database": self.get_secret("azure-sql-database"),
            "username": self.get_secret("azure-sql-username"),
            "password": self.get_secret("azure-sql-password"),
            "connection_string": self.get_secret("azure-sql-connection-string"),
        }

    def get_api_keys(self) -> dict[str, Optional[str]]:
        """
        Retrieve API keys from Key Vault.
        
        Returns:
            Dictionary with API keys
        """
        return {
            "weather_api_key": self.get_secret("weather-api-key"),
            "azure_ad_client_secret": self.get_secret("azure-ad-client-secret"),
            "secret_key": self.get_secret("secret-key"),
        }

    def get_storage_credentials(self) -> dict[str, Optional[str]]:
        """
        Retrieve storage credentials from Key Vault.
        
        Returns:
            Dictionary with storage connection details
        """
        return {
            "account_name": self.get_secret("azure-storage-account-name"),
            "account_key": self.get_secret("azure-storage-account-key"),
            "connection_string": self.get_secret("azure-storage-connection-string"),
        }

    def get_redis_credentials(self) -> dict[str, Optional[str]]:
        """
        Retrieve Redis credentials from Key Vault.
        
        Returns:
            Dictionary with Redis connection details
        """
        return {
            "host": self.get_secret("redis-host"),
            "password": self.get_secret("redis-password"),
            "url": self.get_secret("redis-url"),
        }

