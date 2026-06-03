# URIS-AI

**Urban Risk Intelligence System for Flood-Aware Mobility and Public Service Optimization**

URIS-AI adalah sistem berbasis cloud yang mengintegrasikan data multi-sumber untuk memprediksi dan menganalisis risiko urban secara komprehensif. Sistem ini memantau 25 wilayah di Jakarta dan Jawa Barat, menghitung Urban Risk Score (URS) per wilayah, dan menyajikan informasi melalui dashboard peta interaktif.

> Status proyek: Demo / Simulasi — seluruh data URS bersifat simulasi untuk keperluan presentasi dan pengembangan.

---

## Daftar Isi

- [Fitur Utama](#fitur-utama)
- [Instalasi](#instalasi)
- [Menjalankan Proyek](#menjalankan-proyek)
- [Struktur Folder](#struktur-folder)
- [Teknologi yang Digunakan](#teknologi-yang-digunakan)

---

## Fitur Utama

**Penilaian Risiko Urban (Urban Risk Score)**
Menghitung URS terpadu (0–100) per wilayah menggunakan formula berbobot: risiko banjir (50%), dampak lalu lintas (30%), dan aksesibilitas layanan publik (20%). Hasil dikategorikan menjadi empat level: RENDAH, SEDANG, TINGGI, dan KRITIS.

**Prediksi Risiko Banjir dengan Machine Learning**
Model scikit-learn terlatih yang mengklasifikasikan risiko banjir berdasarkan data historis banjir, curah hujan, elevasi wilayah, dan kapasitas drainase.

**Dashboard Peta Interaktif**
Visualisasi risiko seluruh wilayah secara real-time menggunakan Azure Maps SDK dengan tampilan night style. Setiap wilayah ditampilkan sebagai marker berwarna sesuai kategori risiko, dilengkapi flood overlay untuk wilayah TINGGI dan KRITIS.

**Rekomendasi Tindakan Kontekstual**
Sistem menghasilkan rekomendasi per wilayah berdasarkan kategori URS, mencakup tipe peringatan, rute alternatif, informasi fasilitas, evakuasi, dan alokasi sumber daya, dengan level urgensi Segera, Waspada, dan Siaga.

**Rute Aman**
Pencarian rute dari titik asal ke tujuan yang secara otomatis menghindari wilayah berkategori TINGGI dan KRITIS.

**Tren Historis URS**
Visualisasi tren Urban Risk Score per wilayah dalam rentang waktu 1 hingga 168 jam terakhir, ditampilkan sebagai grafik area (AreaChart) di panel detail wilayah.

**Autentikasi JWT**
Sistem login berbasis JWT (HS256) dengan dua role pengguna: `government` dan `public`. Token berlaku selama 30 menit.

**Monitoring dan Observabilitas**
Health check endpoint (liveness, readiness, performance), request logging, rate limiting per IP, dan integrasi Azure Application Insights.

---

## Instalasi

### Prasyarat

- Python 3.11+
- Node.js 18+ (disarankan v23 via Laragon di Windows)
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

Edit file `.env` dan isi variabel berikut:

```dotenv
# Koneksi database MySQL
AZURE_MYSQL_CONNECTION_STRING=mysql+pymysql://user:password@host/uris-ai-db

# Kunci Azure Maps (dari Azure Portal)
AZURE_MAPS_KEY=your-azure-maps-key

# JWT secret key
SECRET_KEY=your-random-secret-key

# Mode development
APP_ENV=development
DEBUG=true
API_RELOAD=true
AZURE_KEY_VAULT_ENABLED=false
ENABLE_RATE_LIMITING=false
```

### 3. Instalasi Dependensi Backend

```bash
python -m pip install -r requirements.txt
```

### 4. Inisialisasi Database dan Seeding Data

```bash
# Terapkan migrasi schema
python scripts/migrate_data.py

# Seed data awal (25 wilayah, 646 flood events, jalan, fasilitas)
python scripts/seed_data.py

# Generate risk scores
python scripts/generate_risk_scores.py

# Generate data historis URS (24 jam per wilayah)
python scripts/generate_urs_history.py

# Generate rekomendasi tindakan
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

Jalankan backend di terminal pertama:

```bash
# Dari direktori root
python -m uvicorn uris_ai.api.main:app --host 0.0.0.0 --port 8000 --reload
```

Jalankan frontend di terminal kedua:

```bash
cd frontend
npm run dev
```

Frontend tersedia di `http://localhost:5173` dan akan meneruskan request API ke backend di port 8000 melalui Vite dev proxy.

### Production Build

```bash
# Build frontend ke direktori static FastAPI
cd frontend
npm run build

# Jalankan backend (melayani frontend sebagai static files)
python -m uvicorn uris_ai.api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

Akses aplikasi di `http://localhost:8000/dashboard`.

### Windows (PowerShell / Laragon)

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
$env:PATH = "C:\laragon\bin\nodejs\node-v23.3.0-win-x64;" + $env:PATH

# Jalankan backend
python -m uvicorn uris_ai.api.main:app --reload

# Di terminal lain, jalankan frontend
cd frontend
node_modules\.bin\vite.cmd
```

### Akun Default

| Username | Password  | Role       |
| -------- | --------- | ---------- |
| admin    | Admin123! | government |
| public   | Admin123! | public     |

### Endpoint Penting

| Endpoint                       | Keterangan                              |
| ------------------------------ | --------------------------------------- |
| `GET /`                        | Info aplikasi                           |
| `GET /health`                  | Health check dasar                      |
| `GET /health/ready`            | Readiness check (DB + cache)            |
| `GET /api/dashboard`           | Data agregat dashboard (regions + KPI)  |
| `GET /regions/risk`            | URS semua wilayah                       |
| `GET /regions/{id}/risk`       | URS satu wilayah                        |
| `GET /regions/{id}/risk/trend` | Tren historis URS                       |
| `POST /auth/login`             | Login, mendapatkan JWT                  |
| `GET /docs`                    | Dokumentasi API interaktif (Swagger UI) |

---

## Struktur Folder

```
uris-ai/
├── .env                        # Konfigurasi environment (tidak di-commit)
├── .env.example                # Template konfigurasi environment
├── requirements.txt            # Dependensi Python
├── pyproject.toml              # Konfigurasi proyek dan tooling
│
├── src/
│   └── uris_ai/
│       ├── api/
│       │   ├── main.py         # App factory, middleware, endpoint utama
│       │   ├── dependencies.py # Dependency injection (DB, auth, role)
│       │   ├── middleware.py   # RateLimit, RequestLogging, HTTPSRedirect
│       │   ├── schemas.py      # Pydantic request/response schemas
│       │   └── routers/
│       │       ├── auth.py             # POST /auth/login, /auth/logout
│       │       ├── risk.py             # GET /regions/risk, /{id}/risk/trend
│       │       ├── recommendations.py  # GET rekomendasi, POST /routes/safe
│       │       └── users.py            # GET /users/me
│       ├── models/
│       │   ├── database.py     # SQLAlchemy ORM models (8 tabel)
│       │   └── db_utils.py     # Engine factory PyMySQL + SSL
│       ├── ml/
│       │   ├── flood_risk_engine.py        # Klasifikasi kategori risiko
│       │   ├── risk_scoring_engine.py      # Kalkulasi URS dan tren
│       │   └── recommendation_engine.py   # Rekomendasi dan rute aman
│       ├── services/
│       │   ├── auth_service.py  # JWT create/decode, bcrypt verify
│       │   └── cache_service.py # Redis cache wrapper
│       ├── security/
│       │   └── input_validation.py
│       ├── database/
│       │   └── optimization.py  # Manajemen index database
│       ├── utils/
│       │   ├── logging_config.py
│       │   └── monitoring.py    # Application Insights wrapper
│       ├── config.py            # Settings dari .env (pydantic-settings)
│       └── startup.py           # Startup: buat index, cache warming
│
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js          # Dev proxy ke :8000, build ke src/uris_ai/static/
│   ├── tailwind.config.js      # Custom theme Ocean Deep
│   └── src/
│       ├── main.jsx            # Entry: BrowserRouter + QueryClientProvider
│       ├── App.jsx             # Dashboard utama (/dashboard)
│       ├── api.js              # Fetch wrapper ke backend endpoints
│       ├── store.js            # Zustand global state
│       ├── utils.js            # getRiskColor, filterRegions, formatURS
│       ├── components/
│       │   ├── Header.jsx
│       │   ├── KpiCards.jsx
│       │   ├── Map.jsx
│       │   ├── Sidebar.jsx
│       │   ├── DetailPanel.jsx
│       │   ├── DisclaimerModal.jsx
│       │   └── LoadingScreen.jsx
│       └── pages/
│           └── LandingPage.jsx
│
├── models/
│   ├── flood_risk_model.pkl    # Model scikit-learn terlatih
│   ├── flood_risk_scaler.pkl   # Scaler normalisasi fitur
│   └── flood_risk_metadata.json
│
├── data/
│   └── raw/
│       ├── bmkg/               # Data cuaca BMKG (432 record)
│       ├── osm/                # Data jalan dan fasilitas OpenStreetMap
│       ├── historis_banjir/    # Data historis banjir Jakarta
│       ├── petabencana/        # Laporan banjir PetaBencana
│       └── wilayah/            # Data administrasi wilayah
│
├── scripts/                    # Utilitas manajemen data dan deployment
│   ├── seed_data.py
│   ├── migrate_data.py
│   ├── generate_risk_scores.py
│   ├── generate_urs_history.py
│   ├── generate_recommendations.py
│   ├── train_flood_model.py
│   ├── blue_green_deploy.sh
│   ├── rollback_deployment.sh
│   └── run_smoke_tests.sh
│
├── infrastructure/
│   └── terraform/              # Infrastructure as Code (Azure)
│
├── docs/
│   └── project_documentation.md
│
└── logs/
```

---

## Teknologi yang Digunakan

### Backend

| Komponen          | Versi   | Keterangan                        |
| ----------------- | ------- | --------------------------------- |
| Python            | 3.11+   | Runtime utama                     |
| FastAPI           | 0.109.2 | Web framework (ASGI)              |
| Uvicorn           | 0.27.1  | ASGI server                       |
| SQLAlchemy        | 2.0.49  | ORM                               |
| PyMySQL           | 1.1.0   | MySQL driver                      |
| Pydantic          | 2.5.3   | Validasi data dan schema          |
| pydantic-settings | 2.1.0   | Konfigurasi dari environment vars |
| python-jose       | 3.3.0   | JWT token (HS256)                 |
| passlib[bcrypt]   | 1.7.4   | Password hashing                  |
| scikit-learn      | 1.4.0   | Model machine learning            |
| pandas            | 2.2.0   | Pemrosesan data                   |
| numpy             | 1.26.4  | Komputasi numerik                 |
| redis             | 5.0.1   | Cache client (opsional)           |

### Frontend

| Komponen              | Versi  | Keterangan                   |
| --------------------- | ------ | ---------------------------- |
| React                 | 18.3.1 | UI framework                 |
| Vite                  | 5.3.1  | Build tool dan dev server    |
| TailwindCSS           | 3.4.4  | Utility-first CSS framework  |
| @tanstack/react-query | 5.40.0 | Server state management      |
| Zustand               | 4.5.2  | Client state management      |
| azure-maps-control    | 3.3.0  | Peta interaktif (Azure Maps) |
| Recharts              | 2.12.7 | Grafik dan visualisasi data  |
| React Router DOM      | 6.23.1 | Routing SPA                  |

### Cloud dan Infrastruktur

| Layanan                    | Keterangan                          |
| -------------------------- | ----------------------------------- |
| Azure Database for MySQL   | Database utama (Free Tier, B1MS)    |
| Azure Maps                 | Peta interaktif (Gen2, night style) |
| Azure Blob Storage         | Penyimpanan data raw dan processed  |
| Azure Key Vault            | Manajemen secrets                   |
| Azure Application Insights | Monitoring dan telemetri            |
| Terraform                  | Infrastructure as Code              |

### Testing dan Tooling

| Komponen   | Versi  | Keterangan             |
| ---------- | ------ | ---------------------- |
| pytest     | 7.4.4  | Testing framework      |
| hypothesis | 6.96.1 | Property-based testing |
| locust     | 2.20.0 | Load testing           |
| black      | 24.1.1 | Code formatter         |
| ruff       | 0.1.14 | Linter                 |
| mypy       | 1.8.0  | Static type checker    |

---

## Lisensi

Proyek ini dikembangkan untuk keperluan demo dan presentasi. Seluruh data yang digunakan bersifat simulasi.
