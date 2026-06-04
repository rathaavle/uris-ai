# =============================================================================
# Set environment variables di Azure App Service untuk URIS-AI
# EDIT nilai-nilai di bawah sesuai .env kamu sebelum menjalankan!
# =============================================================================

$az = "C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
$RG = "uris-ai-rg"
$APP = "urisai-api"

# Baca nilai dari .env lokal
$envFile = Join-Path $PSScriptRoot "..\\.env"
$envVars = @{}
Get-Content $envFile | ForEach-Object {
    if ($_ -match "^\s*([^#][^=]+)=(.+)$") {
        $key = $Matches[1].Trim()
        $val = $Matches[2].Trim()
        $envVars[$key] = $val
    }
}

Write-Host "Setting environment variables on Azure App Service..." -ForegroundColor Cyan

# Build array of key=value pairs
$settings = @()
foreach ($kv in $envVars.GetEnumerator()) {
    $settings += "$($kv.Key)=$($kv.Value)"
}

# Override beberapa nilai untuk production
$settings += "APP_ENV=production"
$settings += "DEBUG=false"
$settings += "API_RELOAD=false"
$settings += "ENABLE_CACHING=false"
$settings += "ENABLE_RATE_LIMITING=false"
$settings += "ENFORCE_HTTPS=false"
$settings += "PYTHONPATH=/home/site/wwwroot/src"

# Set ke Azure
& $az webapp config appsettings set `
    --name $APP `
    --resource-group $RG `
    --settings @settings

Write-Host "Environment variables set successfully!" -ForegroundColor Green
Write-Host "Run .\scripts\zip_deploy.ps1 to deploy code." -ForegroundColor Yellow
