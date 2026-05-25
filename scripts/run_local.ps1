#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Script untuk menjalankan URIS-AI secara lokal setelah setup Azure selesai.
    Menjalankan API server dan Dashboard secara bersamaan.

.USAGE
    .\scripts\run_local.ps1 [-ApiOnly] [-DashboardOnly] [-SeedData]

.PARAMETERS
    -ApiOnly        Hanya jalankan API server
    -DashboardOnly  Hanya jalankan Dashboard
    -SeedData       Seed data awal ke database sebelum start
#>

param(
    [switch]$ApiOnly,
    [switch]$DashboardOnly,
    [switch]$SeedData
)

$ErrorActionPreference = "Stop"

function Write-Step($msg) {
    Write-Host "`n==> $msg" -ForegroundColor Cyan
}
function Write-OK($msg) {
    Write-Host "    [OK] $msg" -ForegroundColor Green
}
function Write-Fail($msg) {
    Write-Host "    [ERROR] $msg" -ForegroundColor Red
}

# ============================================================
# Cek .env ada
# ============================================================
Write-Step "Mengecek konfigurasi..."
if (-not (Test-Path ".env")) {
    Write-Fail ".env tidak ditemukan. Jalankan setup_azure_windows.ps1 dulu."
    exit 1
}
Write-OK ".env ditemukan"

# ============================================================
# Cek PYTHONPATH
# ============================================================
$env:PYTHONPATH = "src"

# ============================================================
# Test import
# ============================================================
Write-Step "Mengecek dependencies Python..."
$importTest = python -c "from uris_ai.api.main import app; print('OK')" 2>&1
if ($importTest -notmatch "OK") {
    Write-Fail "Import gagal: $importTest"
    Write-Host "    Pastikan semua package terinstall: python -m pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}
Write-OK "Semua dependencies OK"

# ============================================================
# Test koneksi database
# ============================================================
Write-Step "Mengecek koneksi database..."
$dbTest = python -c "
import sys
sys.path.insert(0, 'src')
from uris_ai.config import settings
from uris_ai.models.db_utils import create_db_engine
from sqlalchemy import text
try:
    engine = create_db_engine(settings.azure_sql_connection_string)
    with engine.connect() as conn:
        conn.execute(text('SELECT 1'))
    print('OK')
except Exception as e:
    print(f'FAIL:{e}')
" 2>&1

if ($dbTest -match "^OK") {
    Write-OK "Database terhubung"
} else {
    $errMsg = ($dbTest | Where-Object { $_ -match "FAIL:" }) -replace "FAIL:", ""
    Write-Fail "Database tidak bisa diakses: $errMsg"
    Write-Host ""
    Write-Host "    Kemungkinan penyebab:" -ForegroundColor Yellow
    Write-Host "    1. ODBC Driver 18 belum terinstall -> https://aka.ms/downloadmsodbcsql" -ForegroundColor Yellow
    Write-Host "    2. IP lokal belum di-whitelist di SQL Server firewall" -ForegroundColor Yellow
    Write-Host "    3. Connection string di .env salah" -ForegroundColor Yellow
    Write-Host ""
    $cont = Read-Host "    Lanjut tetap jalankan? [y/N]"
    if ($cont -ne "y" -and $cont -ne "Y") { exit 1 }
}

# ============================================================
# Inisialisasi schema & seed data
# ============================================================
Write-Step "Menginisialisasi schema database..."
python -c "
import sys
sys.path.insert(0, 'src')
from uris_ai.config import settings
from uris_ai.models.database import Base
from uris_ai.models.db_utils import create_db_engine
engine = create_db_engine(settings.azure_sql_connection_string)
Base.metadata.create_all(bind=engine)
print('Schema OK')
" 2>&1 | ForEach-Object { Write-Host "    $_" }

if ($SeedData) {
    Write-Step "Seeding data awal..."
    python scripts/seed_data.py
    Write-OK "Data seeding selesai"
}

# ============================================================
# Jalankan services
# ============================================================
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Menjalankan URIS-AI" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green

if (-not $DashboardOnly) {
    Write-Host ""
    Write-Host "  API Server  : http://localhost:8000" -ForegroundColor White
    Write-Host "  API Docs    : http://localhost:8000/docs" -ForegroundColor White
    Write-Host "  Health Check: http://localhost:8000/health" -ForegroundColor White
}
if (-not $ApiOnly) {
    Write-Host ""
    Write-Host "  Dashboard   : http://localhost:8501" -ForegroundColor White
}
Write-Host ""
Write-Host "  Tekan Ctrl+C untuk menghentikan" -ForegroundColor Yellow
Write-Host ""

if ($ApiOnly) {
    # Jalankan hanya API
    $env:PYTHONPATH = "src"
    python -m uvicorn uris_ai.api.main:app --reload --host 0.0.0.0 --port 8000

} elseif ($DashboardOnly) {
    # Jalankan hanya Dashboard
    $env:PYTHONPATH = "src"
    python -m streamlit run src/uris_ai/dashboard/app.py --server.port 8501 --server.address 0.0.0.0

} else {
    # Jalankan keduanya — API di background, Dashboard di foreground
    $env:PYTHONPATH = "src"
    
    # Start API di window baru
    $apiJob = Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "`$env:PYTHONPATH='src'; python -m uvicorn uris_ai.api.main:app --reload --host 0.0.0.0 --port 8000"
    ) -PassThru -WorkingDirectory (Get-Location)
    
    Write-Host "  API server berjalan di window terpisah (PID: $($apiJob.Id))" -ForegroundColor Green
    Start-Sleep -Seconds 3
    
    # Start Dashboard di window ini
    python -m streamlit run src/uris_ai/dashboard/app.py --server.port 8501 --server.address 0.0.0.0
    
    # Cleanup API process saat dashboard ditutup
    if ($apiJob -and -not $apiJob.HasExited) {
        Write-Host "`n  Menghentikan API server..." -ForegroundColor Yellow
        Stop-Process -Id $apiJob.Id -Force -ErrorAction SilentlyContinue
    }
}
