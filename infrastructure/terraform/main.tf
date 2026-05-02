terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy = true
    }
  }
}

# Variables
variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
  default     = "uris-ai-rg"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "southeastasia"
}

variable "environment" {
  description = "Environment (dev, staging, production)"
  type        = string
  default     = "dev"
}

variable "enable_blue_green" {
  description = "Enable blue-green deployment slots"
  type        = bool
  default     = false
}

variable "deployment_slot_name" {
  description = "Name of the deployment slot for blue-green deployment"
  type        = string
  default     = "green"
}

variable "sql_admin_username" {
  description = "SQL Server admin username"
  type        = string
  default     = "sqladmin"
}

variable "sql_admin_password" {
  description = "SQL Server admin password"
  type        = string
  sensitive   = true
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = var.resource_group_name
  location = var.location

  tags = {
    Environment = var.environment
    Project     = "URIS-AI"
    ManagedBy   = "Terraform"
  }
}

# Storage Account
resource "azurerm_storage_account" "main" {
  name                     = "urisaistorage${var.environment}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"

  tags = {
    Environment = var.environment
    Project     = "URIS-AI"
  }
}

# Blob Containers
resource "azurerm_storage_container" "raw_data" {
  name                  = "raw-data"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

resource "azurerm_storage_container" "processed_data" {
  name                  = "processed-data"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# SQL Server
resource "azurerm_mssql_server" "main" {
  name                         = "uris-ai-sql-server-${var.environment}"
  resource_group_name          = azurerm_resource_group.main.name
  location                     = azurerm_resource_group.main.location
  version                      = "12.0"
  administrator_login          = var.sql_admin_username
  administrator_login_password = var.sql_admin_password
  minimum_tls_version          = "1.2"

  tags = {
    Environment = var.environment
    Project     = "URIS-AI"
  }
}

# SQL Database
resource "azurerm_mssql_database" "main" {
  name           = "uris-ai-db"
  server_id      = azurerm_mssql_server.main.id
  collation      = "SQL_Latin1_General_CP1_CI_AS"
  max_size_gb    = 10
  sku_name       = "S0"
  zone_redundant = false

  tags = {
    Environment = var.environment
    Project     = "URIS-AI"
  }
}

# SQL Firewall Rule - Allow Azure Services
resource "azurerm_mssql_firewall_rule" "azure_services" {
  name             = "AllowAzureServices"
  server_id        = azurerm_mssql_server.main.id
  start_ip_address = "0.0.0.0"
  end_ip_address   = "0.0.0.0"
}

# Key Vault
resource "azurerm_key_vault" "main" {
  name                       = "uris-ai-kv-${var.environment}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = false

  tags = {
    Environment = var.environment
    Project     = "URIS-AI"
  }
}

data "azurerm_client_config" "current" {}

# Key Vault Access Policy
resource "azurerm_key_vault_access_policy" "main" {
  key_vault_id = azurerm_key_vault.main.id
  tenant_id    = data.azurerm_client_config.current.tenant_id
  object_id    = data.azurerm_client_config.current.object_id

  secret_permissions = [
    "Get",
    "List",
    "Set",
    "Delete",
    "Purge",
    "Recover"
  ]
}

# Redis Cache
resource "azurerm_redis_cache" "main" {
  name                = "uris-ai-redis-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  capacity            = 0
  family              = "C"
  sku_name            = "Basic"
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"

  tags = {
    Environment = var.environment
    Project     = "URIS-AI"
  }
}

# App Service Plan
resource "azurerm_service_plan" "main" {
  name                = "uris-ai-asp-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  os_type             = "Linux"
  sku_name            = "B1"

  tags = {
    Environment = var.environment
    Project     = "URIS-AI"
  }
}

# App Service - API
resource "azurerm_linux_web_app" "api" {
  name                = "uris-ai-api-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  service_plan_id     = azurerm_service_plan.main.id

  site_config {
    always_on = false
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    "AZURE_SQL_CONNECTION_STRING"     = "Driver={ODBC Driver 18 for SQL Server};Server=tcp:${azurerm_mssql_server.main.fully_qualified_domain_name},1433;Database=${azurerm_mssql_database.main.name};Uid=${var.sql_admin_username};Pwd=${var.sql_admin_password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    "AZURE_STORAGE_CONNECTION_STRING" = azurerm_storage_account.main.primary_connection_string
    "AZURE_KEY_VAULT_URL"             = azurerm_key_vault.main.vault_uri
    "REDIS_URL"                       = "rediss://:${azurerm_redis_cache.main.primary_access_key}@${azurerm_redis_cache.main.hostname}:${azurerm_redis_cache.main.ssl_port}"
  }

  tags = {
    Environment = var.environment
    Project     = "URIS-AI"
  }
}

# App Service - Dashboard
resource "azurerm_linux_web_app" "dashboard" {
  name                = "uris-ai-dashboard-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  service_plan_id     = azurerm_service_plan.main.id

  site_config {
    always_on = false
    application_stack {
      python_version = "3.11"
    }
  }

  app_settings = {
    "API_URL" = "https://${azurerm_linux_web_app.api.default_hostname}"
  }

  tags = {
    Environment = var.environment
    Project     = "URIS-AI"
  }
}

# Blue-Green Deployment Slots (only for production)
resource "azurerm_linux_web_app_slot" "api_green" {
  count              = var.enable_blue_green ? 1 : 0
  name               = var.deployment_slot_name
  app_service_id     = azurerm_linux_web_app.api.id

  site_config {
    always_on = false
    application_stack {
      python_version = "3.11"
    }
    health_check_path = "/health/ready"
    health_check_eviction_time_in_min = 2
  }

  app_settings = {
    "AZURE_SQL_CONNECTION_STRING"     = "Driver={ODBC Driver 18 for SQL Server};Server=tcp:${azurerm_mssql_server.main.fully_qualified_domain_name},1433;Database=${azurerm_mssql_database.main.name};Uid=${var.sql_admin_username};Pwd=${var.sql_admin_password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
    "AZURE_STORAGE_CONNECTION_STRING" = azurerm_storage_account.main.primary_connection_string
    "AZURE_KEY_VAULT_URL"             = azurerm_key_vault.main.vault_uri
    "REDIS_URL"                       = "rediss://:${azurerm_redis_cache.main.primary_access_key}@${azurerm_redis_cache.main.hostname}:${azurerm_redis_cache.main.ssl_port}"
    "SLOT_NAME"                       = var.deployment_slot_name
  }

  tags = {
    Environment = var.environment
    Project     = "URIS-AI"
    Slot        = var.deployment_slot_name
  }
}

resource "azurerm_linux_web_app_slot" "dashboard_green" {
  count              = var.enable_blue_green ? 1 : 0
  name               = var.deployment_slot_name
  app_service_id     = azurerm_linux_web_app.dashboard.id

  site_config {
    always_on = false
    application_stack {
      python_version = "3.11"
    }
    health_check_path = "/"
    health_check_eviction_time_in_min = 2
  }

  app_settings = {
    "API_URL"   = var.enable_blue_green ? "https://${azurerm_linux_web_app.api.name}-${var.deployment_slot_name}.azurewebsites.net" : "https://${azurerm_linux_web_app.api.default_hostname}"
    "SLOT_NAME" = var.deployment_slot_name
  }

  tags = {
    Environment = var.environment
    Project     = "URIS-AI"
    Slot        = var.deployment_slot_name
  }
}

# Application Insights for monitoring
resource "azurerm_application_insights" "main" {
  name                = "uris-ai-insights-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  application_type    = "web"

  tags = {
    Environment = var.environment
    Project     = "URIS-AI"
  }
}

# Traffic Manager Profile for automatic failover
resource "azurerm_traffic_manager_profile" "main" {
  count                  = var.enable_blue_green ? 1 : 0
  name                   = "uris-ai-tm-${var.environment}"
  resource_group_name    = azurerm_resource_group.main.name
  traffic_routing_method = "Priority"

  dns_config {
    relative_name = "uris-ai-${var.environment}"
    ttl           = 30
  }

  monitor_config {
    protocol                     = "HTTPS"
    port                         = 443
    path                         = "/health/ready"
    interval_in_seconds          = 30
    timeout_in_seconds           = 10
    tolerated_number_of_failures = 3
  }

  tags = {
    Environment = var.environment
    Project     = "URIS-AI"
  }
}

# Traffic Manager Endpoints
resource "azurerm_traffic_manager_azure_endpoint" "api_primary" {
  count              = var.enable_blue_green ? 1 : 0
  name               = "api-primary"
  profile_id         = azurerm_traffic_manager_profile.main[0].id
  target_resource_id = azurerm_linux_web_app.api.id
  priority           = 1
  weight             = 100
}

resource "azurerm_traffic_manager_azure_endpoint" "api_secondary" {
  count              = var.enable_blue_green ? 1 : 0
  name               = "api-secondary"
  profile_id         = azurerm_traffic_manager_profile.main[0].id
  target_resource_id = azurerm_linux_web_app_slot.api_green[0].id
  priority           = 2
  weight             = 100
}

# Outputs
output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "storage_account_name" {
  value = azurerm_storage_account.main.name
}

output "sql_server_fqdn" {
  value = azurerm_mssql_server.main.fully_qualified_domain_name
}

output "key_vault_uri" {
  value = azurerm_key_vault.main.vault_uri
}

output "redis_hostname" {
  value = azurerm_redis_cache.main.hostname
}

output "api_url" {
  value = "https://${azurerm_linux_web_app.api.default_hostname}"
}

output "dashboard_url" {
  value = "https://${azurerm_linux_web_app.dashboard.default_hostname}"
}

output "api_green_slot_url" {
  value = var.enable_blue_green ? "https://${azurerm_linux_web_app.api.name}-${var.deployment_slot_name}.azurewebsites.net" : null
}

output "dashboard_green_slot_url" {
  value = var.enable_blue_green ? "https://${azurerm_linux_web_app.dashboard.name}-${var.deployment_slot_name}.azurewebsites.net" : null
}

output "traffic_manager_fqdn" {
  value = var.enable_blue_green ? azurerm_traffic_manager_profile.main[0].fqdn : null
}

output "application_insights_instrumentation_key" {
  value     = azurerm_application_insights.main.instrumentation_key
  sensitive = true
}

output "application_insights_connection_string" {
  value     = azurerm_application_insights.main.connection_string
  sensitive = true
}
