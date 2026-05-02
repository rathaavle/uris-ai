#!/bin/bash

# URIS-AI Deployment Rollback Script
# Quickly rollback to the previous version in case of issues
# Requirements: 9.2, 9.4

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
RESOURCE_GROUP="${RESOURCE_GROUP:-uris-ai-rg}"
ENVIRONMENT="${ENVIRONMENT:-production}"
API_APP_NAME="uris-ai-api-${ENVIRONMENT}"
DASHBOARD_APP_NAME="uris-ai-dashboard-${ENVIRONMENT}"
SLOT_NAME="${SLOT_NAME:-green}"

echo "=========================================="
echo "URIS-AI Deployment Rollback"
echo "=========================================="
echo ""
log_warning "This will rollback to the previous version"
log_info "Environment: $ENVIRONMENT"
log_info "Resource Group: $RESOURCE_GROUP"
log_info "API App: $API_APP_NAME"
log_info "Dashboard App: $DASHBOARD_APP_NAME"
echo ""

# Check prerequisites
if ! command -v az &> /dev/null; then
    log_error "Azure CLI is not installed."
    exit 1
fi

if ! az account show &> /dev/null; then
    log_error "Not logged in to Azure. Please run: az login"
    exit 1
fi

# Confirm rollback
read -p "Are you sure you want to rollback? (yes/no): " -r
echo ""
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    log_info "Rollback cancelled by user"
    exit 0
fi

# Rollback API
log_info "Rolling back API application..."
az webapp deployment slot swap \
    --resource-group "$RESOURCE_GROUP" \
    --name "$API_APP_NAME" \
    --slot "$SLOT_NAME" \
    --target-slot production

log_success "API rollback completed"

# Wait and verify
sleep 10
PROD_API_URL="https://${API_APP_NAME}.azurewebsites.net"

log_info "Verifying API health..."
if curl -f -s "$PROD_API_URL/health" > /dev/null; then
    log_success "API health check passed"
else
    log_error "API health check failed after rollback"
    exit 1
fi

# Rollback Dashboard
log_info "Rolling back Dashboard application..."
az webapp deployment slot swap \
    --resource-group "$RESOURCE_GROUP" \
    --name "$DASHBOARD_APP_NAME" \
    --slot "$SLOT_NAME" \
    --target-slot production

log_success "Dashboard rollback completed"

echo ""
echo "=========================================="
log_success "Rollback Completed Successfully!"
echo "=========================================="
echo ""
log_info "Production API URL: $PROD_API_URL"
log_info "Production Dashboard URL: https://${DASHBOARD_APP_NAME}.azurewebsites.net"
echo ""
