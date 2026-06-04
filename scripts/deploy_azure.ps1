# =============================================================================
# URIS-AI Deploy to Azure App Service (Free Tier F1)
# Jalankan dari folder root project: d:\project\uris-ai
# =============================================================================

$az = "C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
$RG = "uris-ai-rg"
$PLAN = "urisai-plan"
$APP = "urisai-api"
$LOCATION = "eastus"

Write-Host "=== URIS-AI Azure Deployment ===" -ForegroundColor Cyan

# ---------------------------------------------------------------------------
# Step 1: Build frontend
# ---------------------------------------------------------------------------
Write-Host "`n[1/5] Building React frontend..." -ForegroundColor Yellow
Set-Location frontend
node_modules\.bin\vite.cmd build
Set-Location ..
Write-Host "Frontend build done." -ForegroundColor Green

# ---------------------------------------------------------------------------
# Step 2: Create App Service Plan (Free F1, Linux)
# ---------------------------------------------------------------------------
Write-Host "`n[2/5] Creating App Service Plan (F1 free)..." -ForegroundColor Yellow
& $az appservice plan create `
    --name $PLAN `
    --resource-group $RG `
    --sku F1 `
    --is-linux `
    --location $LOCATION

# ---------------------------------------------------------------------------
# Step 3: Create Web App with Python 3.12
# ---------------------------------------------------------------------------
Write-Host "`n[3/5] Creating Web App..." -ForegroundColor Yellow
& $az webapp create `
    --name $APP `
    --resource-group $RG `
    --plan $PLAN `
    --runtime "PYTHON:3.12"

# ---------------------------------------------------------------------------
# Step 4: Set startup command
# ---------------------------------------------------------------------------
Write-Host "`n[4/5] Configuring startup command..." -ForegroundColor Yellow
& $az webapp config set `
    --name $APP `
    --resource-group $RG `
    --startup-file "python -m uvicorn uris_ai.api.main:app --host 0.0.0.0 --port 8000 --workers 1"

# Set PYTHONPATH agar modul ditemukan
& $az webapp config appsettings set `
    --name $APP `
    --resource-group $RG `
    --settings PYTHONPATH="/home/site/wwwroot/src"

Write-Host "`n[5/5] Done! Now run: .\scripts\set_env_azure.ps1 to configure env vars" -ForegroundColor Green
Write-Host "Then run: .\scripts\zip_deploy.ps1 to deploy the code" -ForegroundColor Green
Write-Host "`nApp URL: https://$APP.azurewebsites.net" -ForegroundColor Cyan
