#!/bin/bash

# URIS-AI Blue-Green Deployment Script
# Implements zero-downtime deployment with automatic rollback capability
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
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
RESOURCE_GROUP="${RESOURCE_GROUP:-uris-ai-rg}"
ENVIRONMENT="${ENVIRONMENT:-production}"
API_APP_NAME="uris-ai-api-${ENVIRONMENT}"
DASHBOARD_APP_NAME="uris-ai-dashboard-${ENVIRONMENT}"
SLOT_NAME="${SLOT_NAME:-green}"
SMOKE_TEST_TIMEOUT=300  # 5 minutes
HEALTH_CHECK_RETRIES=10
HEALTH_CHECK_INTERVAL=5
ROLLBACK_ENABLED="${ROLLBACK_ENABLED:-true}"

echo "=========================================="
echo "URIS-AI Blue-Green Deployment"
echo "=========================================="
echo ""
log_info "Environment: $ENVIRONMENT"
log_info "Resource Group: $RESOURCE_GROUP"
log_info "API App: $API_APP_NAME"
log_info "Dashboard App: $DASHBOARD_APP_NAME"
log_info "Deployment Slot: $SLOT_NAME"
echo ""

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI is not installed."
        exit 1
    fi
    
    if ! az account show &> /dev/null; then
        log_error "Not logged in to Azure. Please run: az login"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Create deployment slot if it doesn't exist
ensure_deployment_slot() {
    local app_name=$1
    local app_type=$2
    
    log_info "Ensuring deployment slot exists for $app_name..."
    
    if ! az webapp deployment slot list \
        --resource-group "$RESOURCE_GROUP" \
        --name "$app_name" \
        --query "[?name=='$SLOT_NAME']" -o tsv | grep -q .; then
        
        log_info "Creating deployment slot: $SLOT_NAME"
        az webapp deployment slot create \
            --resource-group "$RESOURCE_GROUP" \
            --name "$app_name" \
            --slot "$SLOT_NAME" \
            --configuration-source "$app_name"
        
        log_success "Deployment slot created"
    else
        log_info "Deployment slot already exists"
    fi
}

# Build application package
build_application() {
    log_info "Building application package..."
    
    cd "$PROJECT_ROOT"
    
    # Clean previous builds
    rm -f api.zip dashboard.zip
    
    # Build API package
    log_info "Building API package..."
    cd src
    zip -r ../api.zip . -x "*.pyc" -x "__pycache__/*" -x "*.pytest_cache/*" -x "*.hypothesis/*" > /dev/null
    cd ..
    
    log_success "Application package built successfully"
}

# Deploy to green slot
deploy_to_green_slot() {
    local app_name=$1
    local package_file=$2
    
    log_info "Deploying $package_file to green slot of $app_name..."
    
    az webapp deployment source config-zip \
        --resource-group "$RESOURCE_GROUP" \
        --name "$app_name" \
        --slot "$SLOT_NAME" \
        --src "$package_file" \
        --timeout 600
    
    log_success "Deployment to green slot completed"
}

# Health check function
check_health() {
    local url=$1
    local endpoint=$2
    local max_retries=$3
    local interval=$4
    
    log_info "Performing health check on $url$endpoint..."
    
    for i in $(seq 1 "$max_retries"); do
        log_info "Health check attempt $i/$max_retries..."
        
        if curl -f -s -o /dev/null -w "%{http_code}" "$url$endpoint" | grep -q "200"; then
            log_success "Health check passed!"
            return 0
        fi
        
        if [ "$i" -lt "$max_retries" ]; then
            log_warning "Health check failed, retrying in ${interval}s..."
            sleep "$interval"
        fi
    done
    
    log_error "Health check failed after $max_retries attempts"
    return 1
}

# Run smoke tests on green slot
run_smoke_tests() {
    local green_url=$1
    
    log_info "Running smoke tests on green slot..."
    log_info "Green slot URL: $green_url"
    
    # Wait for slot to be ready
    sleep 10
    
    # Test 1: Basic health check
    if ! check_health "$green_url" "/health" 5 5; then
        log_error "Basic health check failed"
        return 1
    fi
    
    # Test 2: Readiness check
    if ! check_health "$green_url" "/health/ready" 5 5; then
        log_error "Readiness check failed"
        return 1
    fi
    
    # Test 3: Liveness check
    if ! check_health "$green_url" "/health/live" 5 5; then
        log_error "Liveness check failed"
        return 1
    fi
    
    # Test 4: Root endpoint
    if ! check_health "$green_url" "/" 3 3; then
        log_error "Root endpoint check failed"
        return 1
    fi
    
    log_success "All smoke tests passed!"
    return 0
}

# Swap deployment slots
swap_slots() {
    local app_name=$1
    
    log_info "Swapping deployment slots for $app_name..."
    log_warning "This will switch traffic from blue (production) to green (staging)"
    
    az webapp deployment slot swap \
        --resource-group "$RESOURCE_GROUP" \
        --name "$app_name" \
        --slot "$SLOT_NAME" \
        --target-slot production
    
    log_success "Slot swap completed"
}

# Monitor production after swap
monitor_production() {
    local prod_url=$1
    local monitoring_duration=$2
    
    log_info "Monitoring production for ${monitoring_duration}s..."
    
    local check_interval=10
    local checks=$((monitoring_duration / check_interval))
    local failed_checks=0
    local max_failed_checks=3
    
    for i in $(seq 1 "$checks"); do
        log_info "Production monitoring check $i/$checks..."
        
        if ! curl -f -s -o /dev/null "$prod_url/health/ready"; then
            failed_checks=$((failed_checks + 1))
            log_warning "Production health check failed ($failed_checks/$max_failed_checks)"
            
            if [ "$failed_checks" -ge "$max_failed_checks" ]; then
                log_error "Production health checks failed $max_failed_checks times"
                return 1
            fi
        else
            log_success "Production health check passed"
            failed_checks=0
        fi
        
        if [ "$i" -lt "$checks" ]; then
            sleep "$check_interval"
        fi
    done
    
    log_success "Production monitoring completed successfully"
    return 0
}

# Rollback deployment
rollback_deployment() {
    local app_name=$1
    
    log_warning "Initiating rollback for $app_name..."
    
    az webapp deployment slot swap \
        --resource-group "$RESOURCE_GROUP" \
        --name "$app_name" \
        --slot "$SLOT_NAME" \
        --target-slot production
    
    log_success "Rollback completed"
}

# Main deployment flow
main() {
    local start_time=$(date +%s)
    
    # Step 1: Check prerequisites
    check_prerequisites
    
    # Step 2: Confirm deployment
    if [ "$ENVIRONMENT" = "production" ]; then
        echo ""
        log_warning "You are about to deploy to PRODUCTION environment"
        read -p "Are you sure you want to continue? (yes/no): " -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            log_info "Deployment cancelled by user"
            exit 0
        fi
    fi
    
    # Step 3: Ensure deployment slots exist
    ensure_deployment_slot "$API_APP_NAME" "api"
    ensure_deployment_slot "$DASHBOARD_APP_NAME" "dashboard"
    
    # Step 4: Build application
    build_application
    
    # Step 5: Deploy to green slot
    deploy_to_green_slot "$API_APP_NAME" "$PROJECT_ROOT/api.zip"
    
    # Step 6: Run smoke tests on green slot
    GREEN_API_URL="https://${API_APP_NAME}-${SLOT_NAME}.azurewebsites.net"
    
    if ! run_smoke_tests "$GREEN_API_URL"; then
        log_error "Smoke tests failed on green slot"
        log_error "Deployment aborted - production environment unchanged"
        exit 1
    fi
    
    # Step 7: Swap slots (blue-green deployment)
    swap_slots "$API_APP_NAME"
    
    # Step 8: Monitor production
    PROD_API_URL="https://${API_APP_NAME}.azurewebsites.net"
    
    if ! monitor_production "$PROD_API_URL" 60; then
        log_error "Production monitoring detected issues"
        
        if [ "$ROLLBACK_ENABLED" = "true" ]; then
            log_warning "Automatic rollback is enabled"
            rollback_deployment "$API_APP_NAME"
            log_error "Deployment failed and was rolled back"
            exit 1
        else
            log_warning "Automatic rollback is disabled"
            log_error "Manual intervention required"
            exit 1
        fi
    fi
    
    # Step 9: Deploy dashboard (after API is stable)
    log_info "Deploying dashboard application..."
    deploy_to_green_slot "$DASHBOARD_APP_NAME" "$PROJECT_ROOT/api.zip"
    
    GREEN_DASHBOARD_URL="https://${DASHBOARD_APP_NAME}-${SLOT_NAME}.azurewebsites.net"
    
    if check_health "$GREEN_DASHBOARD_URL" "/" 5 5; then
        swap_slots "$DASHBOARD_APP_NAME"
        log_success "Dashboard deployed successfully"
    else
        log_warning "Dashboard health check failed, but API is deployed"
    fi
    
    # Step 10: Cleanup
    cd "$PROJECT_ROOT"
    rm -f api.zip dashboard.zip
    
    # Calculate deployment time
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo ""
    echo "=========================================="
    log_success "Deployment Completed Successfully!"
    echo "=========================================="
    echo ""
    log_info "Deployment Duration: ${duration}s"
    log_info "Production API URL: $PROD_API_URL"
    log_info "Production Dashboard URL: https://${DASHBOARD_APP_NAME}.azurewebsites.net"
    log_info "Green Slot API URL: $GREEN_API_URL"
    log_info "Green Slot Dashboard URL: $GREEN_DASHBOARD_URL"
    echo ""
    log_info "The previous version is now in the green slot and can be used for rollback if needed"
    echo ""
}

# Run main function
main "$@"
