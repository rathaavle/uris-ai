#!/usr/bin/env pwsh
<#
.SYNOPSIS  URIS-AI Azure Setup Script untuk Windows
.USAGE     .\scripts\setup_azure_windows.ps1
#>

$ErrorActionPreference = "Stop"

# ============================================================
# HELPER FUNCTIONS
# ============================================================
function Write-Step($msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Write-OK($msg)   { Write-Host "    [OK] $msg" -ForegroundColor Green }
function Write-Skip($msg) { Write-Host "    [SKIP] $msg sudah ada." -ForegroundColor Yellow }
function Write-Fail($msg) { Write-Host "    [ERROR] $msg" -ForegroundColor Red }

# Wrapper az — panggil az.cmd langsung agar bisa jalan di PowerShell
$script:AZ = "C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
function Invoke-Az {
    & $script:AZ @args
}

# ============================================================
# KONFIGURASI
# ============================================================
$SUBSCRIPTION_ID = "579388b1-eb32-4edb-bb83-6061c82834f5"
$TENANT_ID       = "f918ca6a-b004-4e86-b69a-b22f0f3030e2"
$RESOURCE_GROUP  = "uris-ai-rg"
$LOCATION        = "southeastasia"
$APP_PREFIX      = "urisai"

$SQL_SERVER_NAME = "$APP_PREFIX-sql"
$SQL_DB_NAME     = "uris-ai-db"
$SQL_ADMIN_USER  = "sqladmin"
$STORAGE_NAME    = "${APP_PREFIX}storage"
$KEYVAULT_NAME   = "$APP_PREFIX-kv"
$REDIS_NAME      = "$APP_PREFIX-redis"
$SQL_PASSWORD    = $null

# ============================================================
# STEP 0: Cek Azure CLI
# ============================================================
Write-Step "Mengecek Azure CLI..."
if (-not (Test-Path $script:AZ)) {
    Write-Fail "az.cmd tidak ditemukan di $script:AZ"
    Write-Host "    Install dari: https://aka.ms/installazurecliwindows" -ForegroundColor Yellow
    exit 1
}
$azVersion = Invoke-Az version -o tsv 2>$null | Select-Object -First 1
Write-OK "Azure CLI terdeteksi"

# ============================================================
# STEP 1: Cek Login
# ============================================================
Write-Step "Mengecek status login Azure..."
$accountJson = Invoke-Az account show 2>$null
if (-not $accountJson) {
    Write-Host "    Belum login, membuka device code login..." -ForegroundColor Yellow
    Invoke-Az login --tenant $TENANT_ID --use-device-code
}
Invoke-Az account set --subscription $SUBSCRIPTION_ID | Out-Null
$account = (Invoke-Az account show) | ConvertFrom-Json
Write-OK "Login: $($account.user.name)"
Write-OK "Subscription: $($account.name) ($($account.id))"

# ============================================================
# STEP 2: Resource Group
# ============================================================
Write-Step "Mengecek Resource Group '$RESOURCE_GROUP'..."
$rgExists = Invoke-Az group exists --name $RESOURCE_GROUP
if ($rgExists -eq "true") {
    Write-Skip "Resource Group '$RESOURCE_GROUP'"
} else {
    Write-Host "    Membuat Resource Group '$RESOURCE_GROUP' di $LOCATION..." -ForegroundColor White
    Invoke-Az group create --name $RESOURCE_GROUP --location $LOCATION | Out-Null
    Write-OK "Resource Group dibuat"
}

# ============================================================
# STEP 3: SQL Server & Database
# ============================================================
Write-Step "Mengecek SQL Server '$SQL_SERVER_NAME'..."
$sqlExists = Invoke-Az sql server list --resource-group $RESOURCE_GROUP --query "[?name=='$SQL_SERVER_NAME'].name" -o tsv 2>$null
if ($sqlExists) {
    Write-Skip "SQL Server '$SQL_SERVER_NAME'"
    $SQL_SERVER_FQDN = "$SQL_SERVER_NAME.database.windows.net"
    Write-Host "    Masukkan password SQL admin untuk connection string:" -ForegroundColor Yellow
    $secPwd = Read-Host "    Password" -AsSecureString
    $SQL_PASSWORD = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
        [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secPwd))
} else {
    Write-Host "    Membuat SQL Server '$SQL_SERVER_NAME'..." -ForegroundColor White
    $chars = (65..90) + (97..122) + (48..57)
    $SQL_PASSWORD = "Uris@" + (-join ($chars | Get-Random -Count 12 | ForEach-Object {[char]$_}))

    Invoke-Az sql server create `
        --name $SQL_SERVER_NAME `
        --resource-group $RESOURCE_GROUP `
        --location $LOCATION `
        --admin-user $SQL_ADMIN_USER `
        --admin-password $SQL_PASSWORD | Out-Null

    Invoke-Az sql server firewall-rule create `
        --resource-group $RESOURCE_GROUP --server $SQL_SERVER_NAME `
        --name "AllowAzureServices" `
        --start-ip-address 0.0.0.0 --end-ip-address 0.0.0.0 | Out-Null

    try {
        $myIP = (Invoke-RestMethod -Uri "https://api.ipify.org?format=json").ip
        Invoke-Az sql server firewall-rule create `
            --resource-group $RESOURCE_GROUP --server $SQL_SERVER_NAME `
            --name "AllowLocalDev" `
            --start-ip-address $myIP --end-ip-address $myIP | Out-Null
        Write-OK "Firewall rule untuk IP lokal ($myIP) ditambahkan"
    } catch {
        Write-Host "    Tidak bisa detect IP lokal, tambahkan manual di portal Azure" -ForegroundColor Yellow
    }

    $SQL_SERVER_FQDN = "$SQL_SERVER_NAME.database.windows.net"
    Write-OK "SQL Server dibuat: $SQL_SERVER_FQDN"
    Write-Host ""
    Write-Host "    *** SIMPAN PASSWORD INI ***" -ForegroundColor Red
    Write-Host "    SQL Password: $SQL_PASSWORD" -ForegroundColor Magenta
    Write-Host "    ***************************" -ForegroundColor Red
}

Write-Step "Mengecek SQL Database '$SQL_DB_NAME'..."
$dbExists = Invoke-Az sql db list --resource-group $RESOURCE_GROUP --server $SQL_SERVER_NAME --query "[?name=='$SQL_DB_NAME'].name" -o tsv 2>$null
if ($dbExists) {
    Write-Skip "SQL Database '$SQL_DB_NAME'"
} else {
    Write-Host "    Membuat SQL Database (Basic tier)..." -ForegroundColor White
    Invoke-Az sql db create `
        --resource-group $RESOURCE_GROUP --server $SQL_SERVER_NAME `
        --name $SQL_DB_NAME --edition Basic --capacity 5 | Out-Null
    Write-OK "SQL Database dibuat"
}

$SQL_CONN_STR = "Driver={ODBC Driver 18 for SQL Server};Server=tcp:${SQL_SERVER_FQDN},1433;Database=${SQL_DB_NAME};Uid=${SQL_ADMIN_USER};Pwd=${SQL_PASSWORD};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"

# ============================================================
# STEP 4: Storage Account
# ============================================================
Write-Step "Mengecek Storage Account '$STORAGE_NAME'..."
$storageExists = Invoke-Az storage account list --resource-group $RESOURCE_GROUP --query "[?name=='$STORAGE_NAME'].name" -o tsv 2>$null
if ($storageExists) {
    Write-Skip "Storage Account '$STORAGE_NAME'"
} else {
    Write-Host "    Membuat Storage Account..." -ForegroundColor White
    Invoke-Az storage account create `
        --name $STORAGE_NAME --resource-group $RESOURCE_GROUP `
        --location $LOCATION --sku Standard_LRS --kind StorageV2 | Out-Null
    Write-OK "Storage Account dibuat"
}

$STORAGE_KEY = Invoke-Az storage account keys list `
    --resource-group $RESOURCE_GROUP --account-name $STORAGE_NAME `
    --query "[0].value" -o tsv

foreach ($container in @("raw-data", "processed-data")) {
    $exists = Invoke-Az storage container exists `
        --name $container --account-name $STORAGE_NAME --account-key $STORAGE_KEY `
        --query "exists" -o tsv 2>$null
    if ($exists -eq "true") {
        Write-Skip "Container '$container'"
    } else {
        Invoke-Az storage container create --name $container --account-name $STORAGE_NAME --account-key $STORAGE_KEY | Out-Null
        Write-OK "Container '$container' dibuat"
    }
}

$STORAGE_CONN_STR = Invoke-Az storage account show-connection-string `
    --name $STORAGE_NAME --resource-group $RESOURCE_GROUP --query connectionString -o tsv

# ============================================================
# STEP 5: Key Vault
# ============================================================
Write-Step "Mengecek Key Vault '$KEYVAULT_NAME'..."
$kvExists = Invoke-Az keyvault list --resource-group $RESOURCE_GROUP --query "[?name=='$KEYVAULT_NAME'].name" -o tsv 2>$null
if ($kvExists) {
    Write-Skip "Key Vault '$KEYVAULT_NAME'"
} else {
    Write-Host "    Membuat Key Vault..." -ForegroundColor White
    Invoke-Az keyvault create `
        --name $KEYVAULT_NAME --resource-group $RESOURCE_GROUP `
        --location $LOCATION --sku standard | Out-Null
    Write-OK "Key Vault dibuat"
}
$KV_URL = "https://$KEYVAULT_NAME.vault.azure.net/"

# ============================================================
# STEP 6: Redis (opsional)
# ============================================================
Write-Step "Redis Cache (opsional, butuh ~15 menit provisioning)"
$createRedis = Read-Host "    Buat Redis Cache sekarang? [y/N]"

$REDIS_HOST = "localhost"; $REDIS_PORT = "6379"
$REDIS_PASSWORD = ""; $REDIS_URL = "redis://localhost:6379"
$ENABLE_CACHING = "false"

if ($createRedis -eq "y" -or $createRedis -eq "Y") {
    $redisExists = Invoke-Az redis list --resource-group $RESOURCE_GROUP --query "[?name=='$REDIS_NAME'].name" -o tsv 2>$null
    if ($redisExists) {
        Write-Skip "Redis '$REDIS_NAME'"
    } else {
        Invoke-Az redis create --name $REDIS_NAME --resource-group $RESOURCE_GROUP `
            --location $LOCATION --sku Basic --vm-size C0 | Out-Null
        Write-OK "Redis dibuat (provisioning di background)"
    }
    $REDIS_HOST     = Invoke-Az redis show --name $REDIS_NAME --resource-group $RESOURCE_GROUP --query hostName -o tsv
    $REDIS_PORT     = "6380"
    $REDIS_PASSWORD = Invoke-Az redis list-keys --name $REDIS_NAME --resource-group $RESOURCE_GROUP --query primaryKey -o tsv
    $REDIS_URL      = "rediss://:${REDIS_PASSWORD}@${REDIS_HOST}:6380"
    $ENABLE_CACHING = "true"
} else {
    Write-Host "    Skip Redis. Caching dinonaktifkan." -ForegroundColor Yellow
}

# ============================================================
# STEP 7: Generate Secret Key
# ============================================================
Write-Step "Membuat Secret Key JWT..."
$SECRET_KEY = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 64 | ForEach-Object {[char]$_})
Write-OK "Secret Key dibuat"

# ============================================================
# STEP 8: Tulis .env
# ============================================================
Write-Step "Menulis .env..."

if (Test-Path ".env") {
    $backup = ".env.backup.$(Get-Date -Format 'yyyyMMdd_HHmmss')"
    Copy-Item ".env" $backup
    Write-Host "    Backup .env lama -> $backup" -ForegroundColor Yellow
}

@"
# URIS-AI Environment — generated $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')

# Azure
AZURE_SUBSCRIPTION_ID=$SUBSCRIPTION_ID
AZURE_TENANT_ID=$TENANT_ID
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
AZURE_RESOURCE_GROUP=$RESOURCE_GROUP
AZURE_LOCATION=$LOCATION

# SQL Database
AZURE_SQL_SERVER=$SQL_SERVER_NAME
AZURE_SQL_DATABASE=$SQL_DB_NAME
AZURE_SQL_USERNAME=$SQL_ADMIN_USER
AZURE_SQL_PASSWORD=$SQL_PASSWORD
AZURE_SQL_CONNECTION_STRING=$SQL_CONN_STR

# Blob Storage
AZURE_STORAGE_ACCOUNT_NAME=$STORAGE_NAME
AZURE_STORAGE_ACCOUNT_KEY=$STORAGE_KEY
AZURE_STORAGE_CONNECTION_STRING=$STORAGE_CONN_STR
AZURE_STORAGE_CONTAINER_RAW_DATA=raw-data
AZURE_STORAGE_CONTAINER_PROCESSED_DATA=processed-data

# Key Vault
AZURE_KEY_VAULT_NAME=$KEYVAULT_NAME
AZURE_KEY_VAULT_URL=$KV_URL

# Redis
REDIS_HOST=$REDIS_HOST
REDIS_PORT=$REDIS_PORT
REDIS_PASSWORD=$REDIS_PASSWORD
REDIS_URL=$REDIS_URL

# Azure ML (isi jika ada)
AZURE_ML_WORKSPACE_NAME=
AZURE_ML_RESOURCE_GROUP=$RESOURCE_GROUP
AZURE_ML_SUBSCRIPTION_ID=$SUBSCRIPTION_ID

# Azure AD (isi jika ada App Registration)
AZURE_AD_TENANT_ID=$TENANT_ID
AZURE_AD_CLIENT_ID=
AZURE_AD_CLIENT_SECRET=
AZURE_AD_AUTHORITY=https://login.microsoftonline.com/$TENANT_ID

# External APIs
WEATHER_API_URL=https://api.bmkg.go.id/publik/prakiraan-cuaca
WEATHER_API_KEY=
OSM_API_URL=https://overpass-api.de/api/interpreter

# App
APP_NAME=URIS-AI
APP_VERSION=0.1.0
APP_ENV=development
DEBUG=true
LOG_LEVEL=INFO

# API
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1
API_RELOAD=true

# Dashboard
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=8501

# Security
SECRET_KEY=$SECRET_KEY
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENFORCE_HTTPS=false

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Data Ingestion
DATA_FETCH_INTERVAL_MINUTES=10
RISK_CALCULATION_INTERVAL_MINUTES=5

# Model
MODEL_VERSION=1.0.0
MODEL_PATH=models/flood_risk_model.pkl
MODEL_CONFIDENCE_THRESHOLD=0.7

# Monitoring
APPINSIGHTS_INSTRUMENTATION_KEY=
APPINSIGHTS_CONNECTION_STRING=

# Feature Flags
ENABLE_CACHING=$ENABLE_CACHING
ENABLE_RATE_LIMITING=false
ENABLE_MONITORING=false
"@ | Out-File -FilePath ".env" -Encoding utf8 -NoNewline

Write-OK ".env berhasil ditulis"

# ============================================================
# STEP 9: Simpan ke Key Vault
# ============================================================
Write-Step "Menyimpan secrets ke Key Vault..."
try {
    Invoke-Az keyvault secret set --vault-name $KEYVAULT_NAME --name "sql-password"          --value $SQL_PASSWORD  | Out-Null
    Invoke-Az keyvault secret set --vault-name $KEYVAULT_NAME --name "sql-connection-string" --value $SQL_CONN_STR  | Out-Null
    Invoke-Az keyvault secret set --vault-name $KEYVAULT_NAME --name "storage-account-key"   --value $STORAGE_KEY   | Out-Null
    Invoke-Az keyvault secret set --vault-name $KEYVAULT_NAME --name "secret-key"            --value $SECRET_KEY    | Out-Null
    Write-OK "Secrets tersimpan di Key Vault"
} catch {
    Write-Host "    Gagal simpan ke Key Vault: $_" -ForegroundColor Yellow
}

# ============================================================
# STEP 10: Test koneksi & init schema
# ============================================================
Write-Step "Menguji koneksi database..."
$env:PYTHONPATH = "src"
$testResult = python -c "
import sys; sys.path.insert(0,'src')
from uris_ai.config import settings
from uris_ai.models.db_utils import create_db_engine
from sqlalchemy import text
try:
    e = create_db_engine(settings.azure_sql_connection_string)
    with e.connect() as c: c.execute(text('SELECT 1'))
    print('OK')
except Exception as ex: print(f'FAIL:{ex}')
" 2>&1

if ($testResult -match "OK") {
    Write-OK "Koneksi database berhasil"
    Write-Step "Membuat schema database..."
    python -c "
import sys; sys.path.insert(0,'src')
from uris_ai.config import settings
from uris_ai.models.database import Base
from uris_ai.models.db_utils import create_db_engine
e = create_db_engine(settings.azure_sql_connection_string)
Base.metadata.create_all(bind=e)
print('Schema OK')
" 2>&1 | ForEach-Object { Write-Host "    $_" }
} else {
    $err = ($testResult | Where-Object { $_ -match "FAIL:" }) -replace "FAIL:",""
    Write-Host "    Koneksi gagal: $err" -ForegroundColor Red
    Write-Host "    -> Install ODBC Driver 18: https://aka.ms/downloadmsodbcsql" -ForegroundColor Yellow
    Write-Host "    -> Cek firewall SQL Server di portal Azure" -ForegroundColor Yellow
}

# ============================================================
# RINGKASAN
# ============================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  SETUP SELESAI!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Resource Group : $RESOURCE_GROUP" -ForegroundColor White
Write-Host "  SQL Server     : $SQL_SERVER_FQDN" -ForegroundColor White
Write-Host "  Storage        : $STORAGE_NAME" -ForegroundColor White
Write-Host "  Key Vault      : $KV_URL" -ForegroundColor White
Write-Host ""
Write-Host "  Langkah selanjutnya:" -ForegroundColor Cyan
Write-Host "  1. Seed data    : python scripts/seed_data.py" -ForegroundColor Yellow
Write-Host "  2. Run API      : python -m uvicorn uris_ai.api.main:app --reload --port 8000" -ForegroundColor Yellow
Write-Host "  3. Run Dashboard: python -m streamlit run src/uris_ai/dashboard/app.py" -ForegroundColor Yellow
Write-Host "  4. API Docs     : http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
