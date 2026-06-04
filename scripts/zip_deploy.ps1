# =============================================================================
# ZIP Deploy URIS-AI ke Azure App Service
# Jalankan dari folder root: d:\project\uris-ai
# =============================================================================

$az = "C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
$RG = "uris-ai-rg"
$APP = "urisai-api"
$ZIP = "urisai-deploy.zip"

Write-Host "=== URIS-AI ZIP Deploy ===" -ForegroundColor Cyan

# ---------------------------------------------------------------------------
# Step 1: Build frontend
# ---------------------------------------------------------------------------
Write-Host "`n[1/3] Building React frontend..." -ForegroundColor Yellow
Set-Location frontend
node_modules\.bin\vite.cmd build
Set-Location ..
Write-Host "Frontend built to src/uris_ai/static/" -ForegroundColor Green

# ---------------------------------------------------------------------------
# Step 2: Create ZIP (hanya file yang diperlukan)
# ---------------------------------------------------------------------------
Write-Host "`n[2/3] Creating deployment ZIP..." -ForegroundColor Yellow

# Hapus zip lama jika ada
if (Test-Path $ZIP) { Remove-Item $ZIP }

# Buat zip dengan Compress-Archive
$toInclude = @(
    "src",
    "requirements.txt",
    "startup.sh"
)

Compress-Archive -Path $toInclude -DestinationPath $ZIP -Force

$zipSize = (Get-Item $ZIP).Length / 1MB
Write-Host "ZIP created: $ZIP ($([math]::Round($zipSize, 1)) MB)" -ForegroundColor Green

# ---------------------------------------------------------------------------
# Step 3: Deploy ke Azure
# ---------------------------------------------------------------------------
Write-Host "`n[3/3] Deploying to Azure App Service..." -ForegroundColor Yellow
& $az webapp deploy `
    --name $APP `
    --resource-group $RG `
    --src-path $ZIP `
    --type zip

Write-Host "`nDeployment complete!" -ForegroundColor Green
Write-Host "App URL: https://$APP.azurewebsites.net" -ForegroundColor Cyan
Write-Host "Health: https://$APP.azurewebsites.net/health" -ForegroundColor Cyan
Write-Host "API Docs: https://$APP.azurewebsites.net/docs" -ForegroundColor Cyan

# Cleanup
Remove-Item $ZIP
