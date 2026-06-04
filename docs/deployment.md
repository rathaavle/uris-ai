# URIS-AI — Panduan Deploy ke GCP Cloud Run

Dokumen ini menjelaskan langkah-langkah deploy URIS-AI ke Google Cloud Platform menggunakan Cloud Run.

---

## Arsitektur Deploy

```
Developer
    │
    ▼
gcloud builds submit   ──►  GCP Cloud Build  ──►  Artifact Registry
                                                        │
                                                        ▼
                                                  Cloud Run Service
                                                  (asia-southeast1)
                                                        │
                                                        ▼
                                              https://urisai-api-zgwts4p3va-as.a.run.app
                                                        │
                                                        ▼
                                              Azure MySQL (urisai-mysql)
                                              Azure Maps (urisai-maps)
```

**Backend (FastAPI + React static)** di-deploy sebagai Docker container ke Cloud Run.  
**Database (MySQL)** tetap di Azure (Free Tier B1MS) — tidak dimigrasikan ke GCP.

---

## Prasyarat

- [gcloud CLI](https://cloud.google.com/sdk/docs/install) sudah terinstall dan login
- Akun GCP dengan billing aktif (free trial credit cukup)
- Node.js 18+ untuk build frontend

---

## Langkah 1 — Setup GCP Project

```powershell
# Buat project baru
gcloud projects create uris-ai-project --name="URIS-AI"

# Link ke billing account
gcloud billing projects link uris-ai-project --billing-account=BILLING_ACCOUNT_ID

# Set sebagai project aktif
gcloud config set project uris-ai-project

# Enable APIs
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
```

Untuk melihat billing account ID kamu:

```powershell
gcloud billing accounts list
```

---

## Langkah 2 — Buat Artifact Registry

```powershell
gcloud artifacts repositories create urisai-repo \
  --repository-format=docker \
  --location=asia-southeast1 \
  --project=uris-ai-project
```

---

## Langkah 3 — Build Frontend

Sebelum deploy, pastikan build React sudah up-to-date:

```powershell
cd frontend
node_modules\.bin\vite.cmd build   # Windows
# atau
npm run build                       # Linux/Mac
cd ..
```

Output build masuk ke `src/uris_ai/static/` — ikut dalam Docker image.

---

## Langkah 4 — Build Docker Image via Cloud Build

Tidak perlu Docker Desktop lokal. Build dilakukan di cloud GCP:

```powershell
$IMAGE = "asia-southeast1-docker.pkg.dev/uris-ai-project/urisai-repo/urisai-api:latest"
gcloud builds submit . --tag $IMAGE --project=uris-ai-project
```

Build pertama ~3–5 menit (download base image + pip install).  
Build berikutnya lebih cepat karena layer caching.

**File yang di-upload dikontrol oleh `.gcloudignore`** — `frontend/node_modules/` dan `data/` dikecualikan.

---

## Langkah 5 — Deploy ke Cloud Run

```powershell
$IMAGE = "asia-southeast1-docker.pkg.dev/uris-ai-project/urisai-repo/urisai-api:latest"

gcloud run deploy urisai-api `
  --image=$IMAGE `
  --platform=managed `
  --region=asia-southeast1 `
  --allow-unauthenticated `
  --port=8080 `
  --memory=1Gi `
  --cpu=1 `
  --min-instances=0 `
  --max-instances=2 `
  --project=uris-ai-project `
  --set-env-vars="PYTHONPATH=/app/src,APP_ENV=production,..."
```

Lihat bagian [Environment Variables](#environment-variables) untuk daftar lengkap env vars.

---

## Langkah 6 — Konfigurasi MySQL Firewall (Azure)

Cloud Run menggunakan IP publik dinamis. Agar bisa konek ke Azure MySQL, tambahkan firewall rule:

```powershell
$az = "C:\Program Files (x86)\Microsoft SDKs\Azure\CLI2\wbin\az.cmd"
& $az mysql flexible-server firewall-rule create `
  --resource-group uris-ai-rg `
  --name urisai-mysql `
  --rule-name AllowAllIPs `
  --start-ip-address 0.0.0.0 `
  --end-ip-address 255.255.255.255
```

> ⚠️ Rule `0.0.0.0–255.255.255.255` mengizinkan semua IP. Cocok untuk demo. Untuk production, gunakan IP spesifik Cloud Run atau Cloud NAT.

---

## Update / Redeploy

Setiap ada perubahan kode:

```powershell
# 1. Build frontend (jika ada perubahan UI)
cd frontend && node_modules\.bin\vite.cmd build && cd ..

# 2. Build image baru
$IMAGE = "asia-southeast1-docker.pkg.dev/uris-ai-project/urisai-repo/urisai-api:latest"
gcloud builds submit . --tag $IMAGE --project=uris-ai-project

# 3. Deploy ke Cloud Run
gcloud run deploy urisai-api --image=$IMAGE --platform=managed --region=asia-southeast1 --project=uris-ai-project
```

---

## Environment Variables

Semua env vars dikonfigurasi via `--set-env-vars` saat deploy, atau dari GCP Secret Manager.

### Wajib

| Variabel                        | Contoh                                  | Keterangan                              |
| ------------------------------- | --------------------------------------- | --------------------------------------- |
| `PYTHONPATH`                    | `/app/src`                              | Path Python module (wajib di Cloud Run) |
| `APP_ENV`                       | `production`                            | Mode aplikasi                           |
| `AZURE_MYSQL_HOST`              | `urisai-mysql.mysql.database.azure.com` | Host MySQL                              |
| `AZURE_MYSQL_DATABASE`          | `uris-ai-db`                            | Nama database                           |
| `AZURE_MYSQL_USERNAME`          | `mysqladmin`                            | Username MySQL                          |
| `AZURE_MYSQL_PASSWORD`          | `...`                                   | Password MySQL                          |
| `AZURE_MYSQL_CONNECTION_STRING` | `mysql+pymysql://...`                   | Connection string lengkap               |
| `AZURE_MAPS_KEY`                | `...`                                   | Subscription key Azure Maps             |
| `SECRET_KEY`                    | `(random string)`                       | JWT signing key                         |

### Opsional (default aman untuk production)

| Variabel               | Default | Keterangan                                         |
| ---------------------- | ------- | -------------------------------------------------- |
| `DEBUG`                | `false` | Matikan debug mode                                 |
| `API_RELOAD`           | `false` | Matikan hot reload                                 |
| `ENFORCE_HTTPS`        | `false` | Azure handle TLS, jangan redirect di app           |
| `ENABLE_CACHING`       | `false` | Redis tidak dipakai                                |
| `ENABLE_RATE_LIMITING` | `false` | Rate limiting (aktifkan jika perlu)                |
| `ENABLE_MONITORING`    | `false` | Application Insights (aktifkan jika dikonfigurasi) |
| `API_PORT`             | `8080`  | Port Cloud Run                                     |

---

## Struktur Dockerfile

```dockerfile
FROM python:3.12-slim

# Hanya curl untuk healthcheck — PyMySQL pure Python, tidak butuh gcc
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Source code + React build (ada di src/uris_ai/static/)
COPY src/ ./src/

ENV PYTHONPATH=/app/src
ENV PORT=8080

EXPOSE 8080
CMD python -m uvicorn uris_ai.api.main:app --host 0.0.0.0 --port ${PORT} --workers 1
```

---

## Routing SPA

FastAPI melayani React SPA dengan pola berikut:

```
/api/*          → FastAPI routers (JSON API)
/health         → FastAPI health check (JSON)
/docs           → Swagger UI
/assets/*       → Static files (JS/CSS bundle dari React build)
/*.png, *.jpg   → File gambar/logo dari public/ → FileResponse langsung
/*              → SPA catch-all → serve index.html (React Router handle)
```

SPA catch-all logic:

```python
# Jika path punya ekstensi file (.png, .jpg, dll) → cari di STATIC_DIR
if "." in full_path.split("/")[-1]:
    static_file = STATIC_DIR / full_path
    if static_file.exists():
        return FileResponse(str(static_file))
# Semua path lainnya → index.html (React Router)
return FileResponse(STATIC_DIR / "index.html")
```

SPA catch-all **wajib didefinisikan paling akhir** di `main.py`, setelah semua route API, agar `/health` dan `/api/dashboard` tidak ter-intercept.

---

## Monitoring & Logs

Lihat logs Cloud Run:

```powershell
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=urisai-api" \
  --project=uris-ai-project \
  --limit=50 \
  --format="value(textPayload)"
```

Atau buka langsung:

```
https://console.cloud.google.com/logs/viewer?project=uris-ai-project
```

Cek status service:

```powershell
gcloud run services describe urisai-api \
  --region=asia-southeast1 \
  --project=uris-ai-project \
  --format="value(status.url,status.conditions[0].type,status.conditions[0].status)"
```

---

## Troubleshooting

### Container gagal start (`Container failed to start`)

```powershell
# Cek logs revision yang gagal
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.revision_name=REVISION_NAME" \
  --project=uris-ai-project --limit=30 --format="value(textPayload)"
```

**Penyebab umum:**
| Error | Solusi |
|---|---|
| `ModuleNotFoundError: No module named 'uris_ai.models'` | Cek `.gcloudignore` — pastikan `/models/` bukan `models/` (tidak exclude `src/uris_ai/models/`) |
| `Can't connect to MySQL server (timed out)` | Tambah firewall rule Azure MySQL untuk allow all IPs |
| `PORT env var not set` | Pastikan `ENV PORT=8080` ada di Dockerfile dan CMD pakai `${PORT}` |
| Settings validation error | Cek semua required env vars sudah di-set di Cloud Run |

### Traffic masih ke revision lama

```powershell
# Alihkan ke revision terbaru
gcloud run services update-traffic urisai-api \
  --region=asia-southeast1 \
  --project=uris-ai-project \
  --to-latest
```

### `gcloud builds submit` upload terlalu besar

Pastikan `.gcloudignore` ada dan berisi:

```
frontend/node_modules/
data/
/models/
```

Upload harusnya < 10 MB.

---

## Biaya

Menggunakan **GCP free trial credit**:

| Layanan                 | Estimasi                                      |
| ----------------------- | --------------------------------------------- |
| Cloud Run               | $0 (free tier: 2M req/bulan, 360k vCPU-detik) |
| Artifact Registry       | ~$0.10/GB/bulan                               |
| Cloud Build             | 120 menit build gratis/hari                   |
| Azure MySQL (Free B1MS) | $0 (free tier)                                |
| Azure Maps              | ~$0.50/1000 tile request                      |

Dengan traffic rendah (demo), total biaya praktis **$0** menggunakan free trial.

---

## Resource GCP yang Dibuat

| Resource          | Nama              | Region            |
| ----------------- | ----------------- | ----------------- |
| GCP Project       | `uris-ai-project` | —                 |
| Artifact Registry | `urisai-repo`     | `asia-southeast1` |
| Cloud Run Service | `urisai-api`      | `asia-southeast1` |

## Resource Azure yang Tetap Dipakai

| Resource              | Nama            | Keterangan     |
| --------------------- | --------------- | -------------- |
| MySQL Flexible Server | `urisai-mysql`  | Free Tier B1MS |
| Azure Maps            | `urisai-maps`   | Gen2, eastus   |
| Blob Storage          | `urisaistorage` | Data storage   |
| Key Vault             | `urisai-kv`     | Secrets        |
