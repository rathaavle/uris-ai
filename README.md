# URIS-AI

**Urban Risk Intelligence System for Flood-Aware Mobility and Public Service Optimization**

URIS-AI adalah sistem berbasis cloud yang mengintegrasikan data multi-sumber untuk memprediksi dan menganalisis risiko urban. Sistem ini memantau 25 wilayah di Jakarta dan Jawa Barat, menghitung Urban Risk Score (URS) per wilayah, dan menyajikan informasi melalui dashboard peta interaktif.

> **Status:** Demo / Simulasi — seluruh data URS bersifat simulasi untuk keperluan presentasi dan pengembangan.

---

## 🌐 Live Demo

**https://urisai-api-zgwts4p3va-as.a.run.app**

| Halaman            | URL          |
| ------------------ | ------------ |
| Landing Page       | `/`          |
| Dashboard          | `/dashboard` |
| API Docs (Swagger) | `/docs`      |
| Health Check       | `/health`    |

---

## Daftar Isi

- [Fitur Utama](#fitur-utama)
- [Instalasi Lokal](#instalasi-lokal)
- [Menjalankan Proyek](#menjalankan-proyek)
- [Deploy ke GCP Cloud Run](#deploy-ke-gcp-cloud-run)
- [Struktur Folder](#struktur-folder)
- [Teknologi yang Digunakan](#teknologi-yang-digunakan)
- [API Endpoints](#api-endpoints)

---

## Fitur Utama

**Urban Risk Score (URS)**
Menghitung URS terpadu (0–100) per wilayah: risiko banjir (50%), dampak lalu lintas (30%), aksesibilitas layanan publik (20%). Dikategorikan menjadi RENDAH, SEDANG, TINGGI, dan KRITIS.

**Peta Interaktif**
Visualisasi real-time seluruh wilayah menggunakan Azure Maps SDK (night style). Marker berwarna per kategori, flood overlay untuk wilayah risiko tinggi.

**Rekomendasi Tindakan**
Rekomendasi kontekstual per wilayah berdasarkan kategori URS — peringatan, rute alternatif, fasilitas, evakuasi, alokasi sumber daya.

**Tren Historis URS**
Grafik tren Urban Risk Score 24 jam per wilayah (AreaChart) di panel detail.

**Prediksi Banjir ML**
Model scikit-learn terlatih mengklasifikasikan risiko banjir berdasarkan data historis, curah hujan, elevasi, dan kapasitas drainase.

---

## Instalasi Lokal

### Prasyarat

- Python 3.11+
- Node.js 18+ (disarankan v23)
- Akses ke Azure Database for MySQL
- Azure Maps Subscription Key

### 1. Clone Repositori

```bash
git clone https://github.com/rathaavle/uris-ai.git
cd uris-ai
```

### 2. Konfigurasi Environment

```bash
cp .env.example .env
```

Isi variabel utama di `.env`:

```dotenv
AZURE_MYSQL_CONNECTION_STRING=mysql+pymysql://user:password@host/uris-ai-db
AZURE_MAPS_KEY=your-azure-maps-key
SECRET_KEY=your-random-secret-key
APP_ENV=development
DEBUG=true
API_RELOAD=true
ENABLE_CACHING=false
ENABLE_RATE_LIMITING=false
```

### 3. Instalasi Dependensi Backend

```bash
python -m pip install -r requirements.txt
```

### 4. Inisialisasi Database

```bash
python scripts/migrate_data.py
python scripts/seed_data.py
python scripts/generate_risk_scores.py
python scripts/generate_urs_history.py
python scripts/generate_recommendations.py
```

### 5. Instalasi Dependensi Frontend

```bash
cd frontend
npm install
```

---

## Menjalankan Proyek

### Development (Backend + Frontend Terpisah)

Terminal 1 — Backend:

```bash
# Dari direktori root
$env:PYTHONPATH = "src"
python -m uvicorn uris_ai.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Terminal 2 — Frontend:

```bash
cd frontend
node_modules\.bin\vite.cmd        # Windows
# atau
npm run dev                       # Linux/Mac
```

Frontend di `http://localhost:5173`, proxy API ke backend port 8000.

### Production Build (Local)

```bash
cd frontend
node_modules\.bin\vite.cmd build

# Jalankan backend (serve frontend sebagai static files)
$env:PYTHONPATH = "src"
python -m uvicorn uris_ai.api.main:app --host 0.0.0.0 --port 8000
```

---

## Deploy ke GCP Cloud Run

Lihat dokumentasi lengkap: **[docs/deployment.md](docs/deployment.md)**

### Ringkasan Cepat

```bash
# 1. Set project GCP
gcloud config set project uris-ai-project

# 2. Build dan push image
IMAGE="asia-southeast1-docker.pkg.dev/uris-ai-project/urisai-repo/urisai-api:latest"
gcloud builds submit . --tag $IMAGE

# 3. Deploy ke Cloud Run
gcloud run deploy urisai-api \
  --image=$IMAGE \
  --platform=managed \
  --region=asia-southeast1 \
  --allow-unauthenticated \
  --port=8080
```

**Live URL:** `https://urisai-api-zgwts4p3va-as.a.run.app`

---

## Struktur Folder

```
uris-ai/
├── .env                          # Environment variables (tidak di-commit)
├── .env.example                  # Template environment
├── .gcloudignore                 # File yang dikecualikan saat Cloud Build
├── Dockerfile                    # Docker image untuk GCP Cloud Run
├── requirements.txt              # Dependensi Python
├── startup.sh                    # Script startup (referensi)
│
├── src/uris_ai/
│   ├── api/
│   │   ├── main.py               # App factory, middleware, semua endpoint
│   │   ├── dependencies.py       # DI: DB session, auth, role checker
│   │   ├── middleware.py         # RateLimit, RequestLogging, HTTPSRedirect
│   │   ├── schemas.py            # Pydantic schemas
│   │   └── routers/              # auth, risk, recommendations, users
│   ├── models/
│   │   ├── database.py           # SQLAlchemy ORM (8 tabel)
│   │   └── db_utils.py           # Engine factory PyMySQL
│   ├── ml/
│   │   ├── flood_risk_engine.py  # Klasifikasi kategori risiko
│   │   ├── risk_scoring_engine.py
│   │   └── recommendation_engine.py
│   ├── services/
│   │   ├── auth_service.py       # JWT + bcrypt
│   │   └── cache_service.py      # Redis (opsional)
│   ├── utils/
│   │   ├── logging_config.py
│   │   └── monitoring.py         # Application Insights (opsional)
│   ├── static/                   # React build output (npm run build)
│   ├── config.py                 # Settings dari env vars
│   └── startup.py                # Index DB + cache warming
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx               # Dashboard (/dashboard)
│   │   ├── api.js                # Fetch wrapper
│   │   ├── store.js              # Zustand state
│   │   ├── utils.js              # Helper functions
│   │   ├── components/           # Header, Map, Sidebar, DetailPanel, ...
│   │   └── pages/LandingPage.jsx
│   ├── public/                   # Logo dan gambar statis
│   └── vite.config.js            # Dev proxy + build config
│
├── scripts/                      # Utilitas data dan deployment
├── data/raw/                     # Data mentah (BMKG, OSM, PetaBencana)
├── models/                       # ML model pkl files
├── docs/                         # Dokumentasi lengkap
└── infrastructure/terraform/     # IaC untuk Azure resources
```

---

## Teknologi yang Digunakan

### Backend

| Komponen        | Versi   | Keterangan           |
| --------------- | ------- | -------------------- |
| Python          | 3.12    | Runtime              |
| FastAPI         | 0.109.2 | Web framework (ASGI) |
| Uvicorn         | 0.27.1  | ASGI server          |
| SQLAlchemy      | 2.0.49  | ORM                  |
| PyMySQL         | 1.1.0   | MySQL driver         |
| Pydantic        | 2.5.3   | Validasi data        |
| python-jose     | 3.3.0   | JWT (HS256)          |
| passlib[bcrypt] | 1.7.4   | Password hashing     |
| scikit-learn    | 1.4.0   | ML model             |
| pandas          | 2.2.0   | Data processing      |

### Frontend

| Komponen              | Versi  | Keterangan      |
| --------------------- | ------ | --------------- |
| React                 | 18.3.1 | UI framework    |
| Vite                  | 5.4.21 | Build tool      |
| TailwindCSS           | 3.4.4  | Utility CSS     |
| React Router DOM      | 6.23.1 | SPA routing     |
| @tanstack/react-query | 5.40.0 | Server state    |
| Zustand               | 4.5.2  | Client state    |
| azure-maps-control    | 3.3.0  | Peta interaktif |
| Recharts              | 2.12.7 | Grafik          |

### Cloud & Infrastruktur

| Layanan                   | Keterangan                         |
| ------------------------- | ---------------------------------- |
| **GCP Cloud Run**         | Hosting aplikasi (asia-southeast1) |
| **GCP Artifact Registry** | Docker image repository            |
| **GCP Cloud Build**       | CI/CD build pipeline               |
| Azure Database for MySQL  | Database utama (Free Tier B1MS)    |
| Azure Maps                | Peta interaktif (Gen2)             |
| Azure Blob Storage        | Penyimpanan data                   |
| Azure Key Vault           | Secrets management                 |

---

## API Endpoints

| Method | Endpoint                        | Keterangan                        |
| ------ | ------------------------------- | --------------------------------- |
| GET    | `/health`                       | Health check                      |
| GET    | `/api/dashboard`                | Data semua wilayah + KPI          |
| GET    | `/regions/risk`                 | URS semua wilayah                 |
| GET    | `/regions/{id}/risk`            | URS satu wilayah                  |
| GET    | `/regions/{id}/risk/trend`      | Tren historis URS                 |
| GET    | `/regions/{id}/recommendations` | Rekomendasi tindakan              |
| POST   | `/routes/safe`                  | Rute aman (hindari risiko tinggi) |
| GET    | `/docs`                         | Swagger UI                        |

---

## Lisensi

Dikembangkan untuk keperluan demo dan presentasi. Seluruh data bersifat simulasi.

© 2026 URIS-AI
