# Terraform Variables for URIS-AI Infrastructure

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
  
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be one of: dev, staging, production"
  }
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
