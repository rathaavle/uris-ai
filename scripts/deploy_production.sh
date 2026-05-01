#!/bin/bash

# URIS-AI Production Deployment Script (Blue-Green Deployment)

set -e

echo "=========================================="
echo "URIS-AI Production Deployment"
echo "=========================================="
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "Error: Azure CLI is not installed."
    exit 1
fi

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    echo "Not logged in to Azure. Please login..."
    az login
fi

# Variables
RESOURCE_GROUP="uris-ai-rg"
API_APP_NAME="uris-ai-api-production"
DASHBOARD_APP_NAME="uris-ai-dashboard-production"
SLOT_NAME="green"

echo "Deploying to production environment using blue-green deployment..."
echo "Resource Group: $RESOURCE_GROUP"
echo "API App: $API_APP_NAME"
echo "Dashboard App: $DASHBOARD_APP_NAME"
echo "Deployment Slot: $SLOT_NAME"
echo ""

# Confirm deployment
read -p "Are you sure you want to deploy to PRODUCTION? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Create deployment slot if it doesn't exist
echo "Checking deployment slot..."
if ! az webapp deployment slot list \
    --resource-group $RESOURCE_GROUP \
    --name $API_APP_NAME \
    --query "[?name=='$SLOT_NAME']" -o tsv | grep -q .; then
    echo "Creating deployment slot: $SLOT_NAME"
    az webapp deployment slot create \
        --resource-group $RESOURCE_GROUP \
        --name $API_APP_NAME \
        --slot $SLOT_NAME
fi

# Build and deploy API to green slot
echo "Building API application..."
cd src
zip -r ../api.zip . -x "*.pyc" -x "__pycache__/*"
cd ..

echo "Deploying API to green slot..."
az webapp deployment source config-zip \
    --resource-group $RESOURCE_GROUP \
    --name $API_APP_NAME \
    --slot $SLOT_NAME \
    --src api.zip

# Run smoke tests on green slot
echo "Running smoke tests on green slot..."
GREEN_URL="https://$API_APP_NAME-$SLOT_NAME.azurewebsites.net"
if curl -f -s "$GREEN_URL/health" > /dev/null; then
    echo "Smoke tests passed!"
else
    echo "Error: Smoke tests failed. Deployment aborted."
    exit 1
fi

# Swap slots (blue-green deployment)
echo "Swapping deployment slots..."
az webapp deployment slot swap \
    --resource-group $RESOURCE_GROUP \
    --name $API_APP_NAME \
    --slot $SLOT_NAME \
    --target-slot production

# Monitor production for 30 seconds
echo "Monitoring production for 30 seconds..."
sleep 30

# Check production health
PROD_URL="https://$API_APP_NAME.azurewebsites.net"
if curl -f -s "$PROD_URL/health" > /dev/null; then
    echo "Production health check passed!"
else
    echo "Warning: Production health check failed. Consider rollback."
    read -p "Do you want to rollback? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Rolling back..."
        az webapp deployment slot swap \
            --resource-group $RESOURCE_GROUP \
            --name $API_APP_NAME \
            --slot $SLOT_NAME \
            --target-slot production
        echo "Rollback complete."
        exit 1
    fi
fi

# Clean up
rm -f api.zip dashboard.zip

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "Production URL: $PROD_URL"
echo ""
