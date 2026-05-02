#!/bin/bash

# URIS-AI Smoke Test Runner
# Runs smoke tests against a deployed environment
# Requirements: 9.2

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
API_URL="${SMOKE_TEST_API_URL:-http://localhost:8000}"
TIMEOUT="${SMOKE_TEST_TIMEOUT:-30}"
MAX_RETRIES="${SMOKE_TEST_MAX_RETRIES:-3}"
RETRY_DELAY="${SMOKE_TEST_RETRY_DELAY:-5}"

echo "=========================================="
echo "URIS-AI Smoke Tests"
echo "=========================================="
echo ""
log_info "API URL: $API_URL"
log_info "Timeout: ${TIMEOUT}s"
log_info "Max Retries: $MAX_RETRIES"
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    log_error "pytest is not installed. Please install it: pip install pytest"
    exit 1
fi

# Check if requests is installed
if ! python -c "import requests" &> /dev/null; then
    log_error "requests library is not installed. Please install it: pip install requests"
    exit 1
fi

# Wait for API to be ready
log_info "Waiting for API to be ready..."
for i in $(seq 1 "$MAX_RETRIES"); do
    log_info "Attempt $i/$MAX_RETRIES..."
    
    if curl -f -s -o /dev/null "$API_URL/health"; then
        log_success "API is ready!"
        break
    fi
    
    if [ "$i" -eq "$MAX_RETRIES" ]; then
        log_error "API is not responding after $MAX_RETRIES attempts"
        exit 1
    fi
    
    log_warning "API not ready, retrying in ${RETRY_DELAY}s..."
    sleep "$RETRY_DELAY"
done

# Run smoke tests
log_info "Running smoke tests..."
echo ""

cd "$PROJECT_ROOT"

export SMOKE_TEST_API_URL="$API_URL"
export SMOKE_TEST_TIMEOUT="$TIMEOUT"
export SMOKE_TEST_MAX_RETRIES="$MAX_RETRIES"
export SMOKE_TEST_RETRY_DELAY="$RETRY_DELAY"

if pytest tests/smoke/test_deployment_smoke.py \
    -v \
    --tb=short \
    --color=yes \
    -m smoke \
    --junit-xml=smoke-test-results.xml; then
    
    echo ""
    echo "=========================================="
    log_success "All Smoke Tests Passed!"
    echo "=========================================="
    echo ""
    exit 0
else
    echo ""
    echo "=========================================="
    log_error "Smoke Tests Failed!"
    echo "=========================================="
    echo ""
    exit 1
fi
