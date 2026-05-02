# Terraform Outputs for URIS-AI Infrastructure

output "resource_group_name" {
  description = "Name of the resource group"
  value       = azurerm_resource_group.main.name
}

output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.main.name
}

output "sql_server_fqdn" {
  description = "Fully qualified domain name of the SQL Server"
  value       = azurerm_mssql_server.main.fully_qualified_domain_name
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = azurerm_key_vault.main.vault_uri
}

output "redis_hostname" {
  description = "Hostname of the Redis cache"
  value       = azurerm_redis_cache.main.hostname
}

output "api_url" {
  description = "URL of the API application"
  value       = "https://${azurerm_linux_web_app.api.default_hostname}"
}

output "dashboard_url" {
  description = "URL of the Dashboard application"
  value       = "https://${azurerm_linux_web_app.dashboard.default_hostname}"
}

output "api_green_slot_url" {
  description = "URL of the API green deployment slot"
  value       = var.enable_blue_green ? "https://${azurerm_linux_web_app.api.name}-${var.deployment_slot_name}.azurewebsites.net" : null
}

output "dashboard_green_slot_url" {
  description = "URL of the Dashboard green deployment slot"
  value       = var.enable_blue_green ? "https://${azurerm_linux_web_app.dashboard.name}-${var.deployment_slot_name}.azurewebsites.net" : null
}

output "traffic_manager_fqdn" {
  description = "FQDN of the Traffic Manager profile"
  value       = var.enable_blue_green ? azurerm_traffic_manager_profile.main[0].fqdn : null
}

output "application_insights_instrumentation_key" {
  description = "Application Insights instrumentation key"
  value       = azurerm_application_insights.main.instrumentation_key
  sensitive   = true
}

output "application_insights_connection_string" {
  description = "Application Insights connection string"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}
