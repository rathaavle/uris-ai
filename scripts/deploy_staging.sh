#!/bin/bash

# URIS-AI Staging Deployment Script

set -e

echo "=========================================="
echo "URIS-AI Staging Deployment"
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
API_APP_NAME="uris-ai-api-staging"
DASHBOARD_APP_NAME="uris-ai-dashboard-staging"

echo "Deploying to staging environment..."
echo "Resource Group: $RESOURCE_GROUP"
echo "API App: $API_APP_NAME"
echo "Dashboard App: $DASHBOARD_APP_NAME"
echo ""

# Build and deploy API
echo "Building API application..."
cd src
zip -r ../api.zip . -x "*.pyc" -x "__pycache__/*"
cd ..

echo "Deploying API to Azure App Service..."
az webapp deployment source config-zip \
    --resource-group $RESOURCE_GROUP \
    --name $API_APP_NAME \
    --src api.zip

# Build and deploy Dashboard
echo "Building Dashboard application..."
cd src
zip -r ../dashboard.zip . -x "*.pyc" -x "__pycache__/*"
cd ..

echo "Deploying Dashboard to Azure App Service..."
az webapp deployment source config-zip \
    --resource-group $RESOURCE_GROUP \
    --name $DASHBOARD_APP_NAME \
    --src dashboard.zip

# Clean up
rm -f api.zip dashboard.zip

echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo ""
echo "API URL: https://$API_APP_NAME.azurewebsites.net"
echo "Dashboard URL: https://$DASHBOARD_APP_NAME.azurewebsites.net"
echo ""
