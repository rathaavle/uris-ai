"""
Configuration management for URIS-AI application.
Loads settings from environment variables and .env file.
Supports Azure Key Vault integration for secrets management.

Requirements: 10.5
"""

import logging
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    
    # Flag to enable Key Vault integration
    use_key_vault: bool = Field(
        default=False, 
        description="Enable Azure Key Vault for secrets management"
    )

    # Azure Configuration
    azure_subscription_id: Optional[str] = Field(None, description="Azure subscription ID")
    azure_tenant_id: Optional[str] = Field(None, description="Azure tenant ID")
    azure_client_id: Optional[str] = Field(None, description="Azure client ID")
    azure_client_secret: Optional[str] = Field(None, description="Azure client secret")
    azure_resource_group: str = Field(
        default="uris-ai-rg", description="Azure resource group name"
    )
    azure_location: str = Field(default="southeastasia", description="Azure region")

    # Azure Database for MySQL (Free Tier — Flexible Server B1MS)
    azure_mysql_host: Optional[str] = Field(None, description="MySQL server hostname")
    azure_mysql_port: int = Field(default=3306, description="MySQL port")
    azure_mysql_database: Optional[str] = Field(None, description="MySQL database name")
    azure_mysql_username: Optional[str] = Field(None, description="MySQL username")
    azure_mysql_password: Optional[str] = Field(None, description="MySQL password")
    azure_mysql_connection_string: Optional[str] = Field(None, description="MySQL SQLAlchemy URL")

    # Azure Blob Storage
    azure_storage_account_name: Optional[str] = Field(None, description="Azure Storage account name")
    azure_storage_account_key: Optional[str] = Field(None, description="Azure Storage account key")
    azure_storage_connection_string: Optional[str] = Field(
        None, description="Azure Storage connection string"
    )
    azure_storage_container_raw_data: str = Field(
        default="raw-data", description="Container for raw data"
    )
    azure_storage_container_processed_data: str = Field(
        default="processed-data", description="Container for processed data"
    )

    # Azure Key Vault
    azure_key_vault_name: Optional[str] = Field(None, description="Azure Key Vault name")
    azure_key_vault_url: Optional[str] = Field(None, description="Azure Key Vault URL")

    # Azure Cache for Redis
    redis_host: Optional[str] = Field(None, description="Redis host")
    redis_port: int = Field(default=6380, description="Redis port")
    redis_password: Optional[str] = Field(None, description="Redis password")
    redis_url: Optional[str] = Field(None, description="Redis connection URL")

    # Azure Machine Learning
    azure_ml_workspace_name: Optional[str] = Field(None, description="Azure ML workspace name")
    azure_ml_resource_group: Optional[str] = Field(None, description="Azure ML resource group")
    azure_ml_subscription_id: Optional[str] = Field(None, description="Azure ML subscription ID")

    # Azure Active Directory
    azure_ad_tenant_id: Optional[str] = Field(None, description="Azure AD tenant ID")
    azure_ad_client_id: Optional[str] = Field(None, description="Azure AD client ID")
    azure_ad_client_secret: Optional[str] = Field(None, description="Azure AD client secret")
    azure_ad_authority: Optional[str] = Field(None, description="Azure AD authority URL")

    # External APIs
    weather_api_url: str = Field(
        default="https://api.bmkg.go.id/publik/prakiraan-cuaca",
        description="Weather API URL",
    )
    weather_api_key: Optional[str] = Field(None, description="Weather API key")
    osm_api_url: str = Field(
        default="https://overpass-api.de/api/interpreter", description="OSM API URL"
    )
    azure_maps_key: Optional[str] = Field(None, description="Azure Maps subscription key")
    azure_maps_tileset: str = Field(
        default="microsoft.base.road", description="Azure Maps tileset ID"
    )

    # Application Configuration
    app_name: str = Field(default="URIS-AI", description="Application name")
    app_version: str = Field(default="0.1.0", description="Application version")
    app_env: str = Field(default="development", description="Application environment")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_workers: int = Field(default=4, description="Number of API workers")
    api_reload: bool = Field(default=False, description="Auto-reload on code changes")

    # Dashboard Configuration
    dashboard_host: str = Field(default="0.0.0.0", description="Dashboard host")
    dashboard_port: int = Field(default=8501, description="Dashboard port")

    # Security
    secret_key: str = Field(
        default="urisai-default-secret-change-in-production-2024",
        description="Secret key for JWT"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30, description="Access token expiration in minutes"
    )
    
    # HTTPS/TLS Configuration
    enforce_https: bool = Field(
        default=True, description="Enforce HTTPS redirects"
    )
    ssl_cert_file: Optional[str] = Field(
        None, description="Path to SSL certificate file"
    )
    ssl_key_file: Optional[str] = Field(
        None, description="Path to SSL private key file"
    )
    ssl_ca_file: Optional[str] = Field(
        None, description="Path to CA certificate file"
    )

    # Rate Limiting
    rate_limit_per_minute: int = Field(
        default=60, description="Rate limit per minute per user"
    )
    rate_limit_per_hour: int = Field(default=1000, description="Rate limit per hour per user")

    # Data Ingestion
    data_fetch_interval_minutes: int = Field(
        default=10, description="Data fetch interval in minutes"
    )
    risk_calculation_interval_minutes: int = Field(
        default=5, description="Risk calculation interval in minutes"
    )

    # Model Configuration
    model_version: str = Field(default="1.0.0", description="Model version")
    model_path: str = Field(
        default="models/flood_risk_model.pkl", description="Model file path"
    )
    model_confidence_threshold: float = Field(
        default=0.7, description="Model confidence threshold"
    )

    # Monitoring
    appinsights_instrumentation_key: Optional[str] = Field(
        None, description="Application Insights instrumentation key"
    )
    appinsights_connection_string: Optional[str] = Field(
        None, description="Application Insights connection string"
    )

    # Feature Flags
    enable_caching: bool = Field(default=True, description="Enable caching")
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    enable_monitoring: bool = Field(default=True, description="Enable monitoring")


# Global settings instance
settings = Settings()


def load_secrets_from_key_vault(settings_instance: Settings) -> None:
    """
    Load secrets from Azure Key Vault and update settings.
    
    This function should be called during application startup if
    use_key_vault is enabled.
    
    Args:
        settings_instance: Settings instance to update
        
    Requirements: 10.5
    """
    if not settings_instance.use_key_vault:
        logger.info("Key Vault integration disabled")
        return
    
    try:
        from uris_ai.services.key_vault_service import KeyVaultService
        
        kv_service = KeyVaultService(settings_instance.azure_key_vault_url)
        
        # Load database credentials
        db_creds = kv_service.get_database_credentials()
        if db_creds.get("password"):
            settings_instance.azure_mysql_password = db_creds["password"]
        if db_creds.get("connection_string"):
            settings_instance.azure_mysql_connection_string = db_creds["connection_string"]
        
        # Load API keys
        api_keys = kv_service.get_api_keys()
        if api_keys.get("weather_api_key"):
            settings_instance.weather_api_key = api_keys["weather_api_key"]
        if api_keys.get("azure_ad_client_secret"):
            settings_instance.azure_ad_client_secret = api_keys["azure_ad_client_secret"]
        if api_keys.get("secret_key"):
            settings_instance.secret_key = api_keys["secret_key"]
        
        # Load storage credentials
        storage_creds = kv_service.get_storage_credentials()
        if storage_creds.get("account_key"):
            settings_instance.azure_storage_account_key = storage_creds["account_key"]
        if storage_creds.get("connection_string"):
            settings_instance.azure_storage_connection_string = storage_creds["connection_string"]
        
        # Load Redis credentials
        redis_creds = kv_service.get_redis_credentials()
        if redis_creds.get("password"):
            settings_instance.redis_password = redis_creds["password"]
        if redis_creds.get("url"):
            settings_instance.redis_url = redis_creds["url"]
        
        logger.info("Successfully loaded secrets from Azure Key Vault")
        
    except Exception as exc:
        logger.error(f"Failed to load secrets from Key Vault: {exc}", exc_info=True)
        logger.warning("Falling back to environment variables for secrets")

