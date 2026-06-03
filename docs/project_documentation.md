# URIS-AI — Dokumentasi Proyek

**Urban Risk Intelligence System for Flood-Aware Mobility and Public Service Optimization**

> _From Data to Decision for Smarter Urban Resilience_

---

## Daftar Isi

1. [Gambaran Umum](#1-gambaran-umum)
2. [Arsitektur Sistem](#2-arsitektur-sistem)
3. [Stack Teknologi](#3-stack-teknologi)
4. [Infrastruktur Azure](#4-infrastruktur-azure)
5. [Database & Skema](#5-database--skema)
6. [Data & Seeding](#6-data--seeding)
7. [Backend — FastAPI](#7-backend--fastapi)
8. [Frontend — React](#8-frontend--react)
9. [Machine Learning](#9-machine-learning)
10. [Autentikasi & Otorisasi](#10-autentikasi--otorisasi)
11. [Urban Risk Score (URS)](#11-urban-risk-score-urs)
12. [Komponen Dashboard](#12-komponen-dashboard)
13. [Scripts Utilitas](#13-scripts-utilitas)
14. [Konfigurasi & Environment](#14-konfigurasi--environment)
15. [Status Fitur](#15-status-fitur)
16. [Cara Menjalankan Lokal](#16-cara-menjalankan-lokal)

---

## 1. Gambaran Umum

URIS-AI adalah sistem berbasis cloud yang mengintegrasikan data multi-sumber untuk memprediksi dan menganalisis risiko urban secara komprehensif. Sistem ini memantau **25 wilayah** di Jakarta dan Jawa Barat, menghitung Urban Risk Score (URS) per wilayah, dan menyajikan informasi melalui dashboard peta interaktif.

**Tujuan utama:**
- Prediksi risiko banjir per wilayah menggunakan model ML
- Menghitung dampak banjir terhadap lalu lintas dan aksesibilitas fasilitas publik
- Menyajikan Urban Risk Score terpadu (0-100) sebagai indikator prioritas
- Memberikan rekomendasi tindakan yang kontekstual berdasarkan kategori risiko
- Menyediakan rute aman yang menghindari wilayah risiko Tinggi dan Kritis

**Status proyek:** Demo / Simulasi — seluruh data URS bersifat simulasi untuk keperluan presentasi dan pengembangan.

---

## 2. Arsitektur Sistem

```
CLIENT LAYER
  React 18 + Vite 5  <->  Vite Dev Proxy (:5173)
  Azure Maps SDK (atlas)

API LAYER
  FastAPI (Python 3.11)  —  uvicorn  —  port 8000
  Middleware: CORS, RateLimit, RequestLogging, HTTPSRedirect
  Routers: /auth, /users, /regions, /routes

DATA LAYER
  Azure Database for MySQL (Free Tier — B1MS)
  Host: urisai-mysql.mysql.database.azure.com
  DB: uris-ai-db
  Redis Cache (opsional — dinonaktifkan di dev lokal)
  Azure Blob Storage: urisaistorage
  Azure Key Vault: urisai-kv
```

**Catatan deployment:**
- Backend dan frontend berjalan terpisah saat development (uvicorn + Vite dev server)
- Build produksi: `npm run build` menghasilkan output ke `src/uris_ai/static/` yang di-serve FastAPI sebagai StaticFiles

---

## 3. Stack Teknologi

### Backend
| Komponen | Versi | Keterangan |
|---|---|---|
| Python | 3.11+ | Runtime utama |
| FastAPI | 0.109.2 | Web framework |
| Uvicorn | 0.27.1 | ASGI server |
| SQLAlchemy | 2.0.49 | ORM |
| PyMySQL | 1.1.0 | MySQL driver (tanpa ODBC) |
| Pydantic | 2.5.3 | Data validation |
| pydantic-settings | 2.1.0 | Config dari env vars |
| python-jose | 3.3.0 | JWT token |
| passlib[bcrypt] | 1.7.4 | Password hashing |
| python-multipart | 0.0.6 | Form data (OAuth2) |
| scikit-learn | 1.4.0 | ML model |
| pandas | 2.2.0 | Data processing |
| numpy | 1.26.4 | Numerik |
| redis | 5.0.1 | Cache client |
| opencensus-ext-azure | 1.1.15 | Application Insights |
| azure-identity | 1.25.3 | Azure auth |
| azure-keyvault-secrets | 4.11.0 | Key Vault |
| azure-storage-blob | 12.28.0 | Blob storage |
| requests | 2.31.0 | HTTP client |

### Frontend
| Komponen | Versi | Keterangan |
|---|---|---|
| React | 18.3.1 | UI framework |
| React DOM | 18.3.1 | DOM renderer |
| React Router DOM | 6.23.1 | Routing SPA |
| Vite | 5.3.1 | Build tool + dev server |
| TailwindCSS | 3.4.4 | Utility CSS |
| PostCSS | 8.4.38 | CSS processor |
| Autoprefixer | 10.4.19 | CSS vendor prefix |
| @tanstack/react-query | 5.40.0 | Server state management |
| Zustand | 4.5.2 | Client state management |
| azure-maps-control | 3.3.0 | Peta interaktif |
| Recharts | 2.12.7 | Chart/grafik |
| clsx | 2.1.1 | Class name utility |
| @vitejs/plugin-react | 4.3.1 | Vite React plugin |

### DevOps & Testing
| Komponen | Keterangan |
|---|---|
| Terraform | Infrastructure as Code |
| pytest 7.4.4 | Testing framework |
| pytest-asyncio 0.23.3 | Async test support |
| hypothesis 6.96.1 | Property-based testing |
| locust 2.20.0 | Load testing |
| black 24.1.1 | Code formatter |
| ruff 0.1.14 | Linter |
| mypy 1.8.0 | Static type checker |

---

## 4. Infrastruktur Azure

### Resource Group
- **Nama:** `uris-ai-rg`
- **Region:** `southeastasia` (Singapore)

### Layanan Azure Aktif

| Layanan | Nama Resource | Keterangan |
|---|---|---|
| Azure Database for MySQL | `urisai-mysql` | Free Tier, B1MS |
| Azure Blob Storage | `urisaistorage` | Data raw & processed |
| Azure Key Vault | `urisai-kv` | Secrets management |
| Azure Maps | `urisai-maps` | Gen2, region: eastus |

### Azure Database for MySQL
- **Host:** `urisai-mysql.mysql.database.azure.com`
- **Database:** `uris-ai-db`
- **Username:** `mysqladmin`
- **Tier:** Free Tier (B1MS)
- **Koneksi:** PyMySQL dengan SSL via `creator` function pattern
- **Migrasi:** Sebelumnya menggunakan Azure SQL Server (paid), dimigrasikan ke MySQL free tier

### Azure Maps
- **Nama:** `urisai-maps`
- **Generasi:** Gen2
- **Region:** `eastus`
- **Digunakan untuk:** Peta interaktif night style di dashboard
- **Auth:** Subscription Key — dikirim ke frontend via `/api/dashboard`

### Redis Cache
- **Status di lokal:** Dinonaktifkan (Error 10061 — tidak ada Redis lokal)
- **Behavior:** Sistem beroperasi normal tanpa cache (fallback ke DB langsung)

### Application Insights
- **Status di lokal:** Dinonaktifkan (connection string tidak dikonfigurasi)
- **Behavior:** Telemetri dilewati, tidak mempengaruhi fungsi utama

---

## 5. Database & Skema

### Jumlah Tabel: 8

#### `regions`
| Kolom | Tipe | Keterangan |
|---|---|---|
| region_id | INT PK | ID wilayah |
| name | VARCHAR(255) | Nama kecamatan |
| latitude | FLOAT | Koordinat lintang |
| longitude | FLOAT | Koordinat bujur |
| elevation | FLOAT nullable | Ketinggian (meter) |
| drainage_capacity | FLOAT nullable | Kapasitas drainase |
| created_at | DATETIME | Waktu dibuat |
| updated_at | DATETIME | Waktu diperbarui |

#### `weather_data`
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | INT PK auto | ID data |
| region_id | INT FK | Referensi ke regions |
| date | DATETIME | Tanggal/waktu observasi |
| rainfall | FLOAT | Curah hujan |
| humidity | FLOAT | Kelembaban |
| temperature | FLOAT | Suhu |
| wind_speed | FLOAT nullable | Kecepatan angin |
Index: `idx_weather_region_date` (region_id, date)

#### `flood_events`
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | INT PK auto | ID event |
| region_id | INT FK | Referensi ke regions |
| date | DATETIME | Tanggal kejadian |
| severity | INT | Tingkat keparahan (1-4) |
| water_level | FLOAT nullable | Tinggi muka air (cm) |
| duration_hours | INT nullable | Durasi banjir (jam) |
| affected_area_km2 | FLOAT nullable | Luas terdampak (km2) |
Constraint: `severity BETWEEN 1 AND 4`
Index: `idx_flood_region_date` (region_id, date)

#### `roads`
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | INT PK auto | ID jalan |
| region_id | INT FK | Referensi ke regions |
| road_name | VARCHAR(255) nullable | Nama jalan |
| road_type | VARCHAR(50) nullable | Tipe: primary/secondary/tertiary/residential |
| road_density | FLOAT | Kepadatan jalan |
| length_km | FLOAT nullable | Panjang (km) |
| is_main_road | BOOLEAN | Apakah jalan utama |

#### `public_facilities`
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | INT PK auto | ID fasilitas |
| region_id | INT FK | Referensi ke regions |
| name | VARCHAR(255) | Nama fasilitas |
| type | VARCHAR(50) | Tipe: hospital/clinic/school/government |
| latitude | FLOAT | Koordinat lintang |
| longitude | FLOAT | Koordinat bujur |
| capacity | INT nullable | Kapasitas |
| is_operational | BOOLEAN | Status operasional |
Index: `idx_region_type` (region_id, type)

#### `risk_scores`
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | INT PK auto | ID skor |
| region_id | INT FK | Referensi ke regions |
| date | DATETIME | Waktu kalkulasi |
| flood_risk | FLOAT | Skor risiko banjir (0-100) |
| traffic_impact | FLOAT | Skor dampak lalu lintas (0-100) |
| service_access | FLOAT | Skor aksesibilitas layanan (0-100) |
| urban_risk_score | FLOAT | URS terpadu (0-100) |
Constraint: semua skor `BETWEEN 0 AND 100`
Index: `idx_risk_region_date`, `idx_urs`

#### `recommendations`
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | INT PK auto | ID rekomendasi |
| region_id | INT FK | Referensi ke regions |
| recommendation_type | VARCHAR(50) | Tipe: alert/route/service/evacuation/resource_allocation |
| description | TEXT | Deskripsi rekomendasi |
| urgency_level | VARCHAR(20) | Level: Segera/Waspada/Siaga |
| created_at | DATETIME | Waktu dibuat |
| expires_at | DATETIME nullable | Waktu kedaluwarsa |
| is_active | BOOLEAN | Status aktif |
Index: `idx_region_active`, `idx_urgency`

#### `users`
| Kolom | Tipe | Keterangan |
|---|---|---|
| id | INT PK auto | ID user |
| username | VARCHAR(100) UNIQUE | Nama pengguna |
| email | VARCHAR(255) UNIQUE | Email |
| password_hash | VARCHAR(255) | Hash bcrypt |
| role | VARCHAR(50) | Role: public/government |
| created_at | DATETIME | Waktu dibuat |
| last_login | DATETIME nullable | Login terakhir |
| is_active | BOOLEAN | Status aktif |

---

## 6. Data & Seeding

### Wilayah (25 total)

#### Jakarta (15 kecamatan)
| Kecamatan | Kota | Elevasi (m) | Drainage Capacity |
|---|---|---|---|
| Menteng | Jakarta Pusat | 7.0 | 150.0 |
| Tanah Abang | Jakarta Pusat | 5.0 | 120.0 |
| Kemayoran | Jakarta Pusat | 8.0 | 180.0 |
| Kelapa Gading | Jakarta Utara | 3.0 | 100.0 |
| Penjaringan | Jakarta Utara | 2.0 | 80.0 |
| Pademangan | Jakarta Utara | 4.0 | 110.0 |
| Kebayoran Baru | Jakarta Selatan | 15.0 | 200.0 |
| Tebet | Jakarta Selatan | 12.0 | 170.0 |
| Cilandak | Jakarta Selatan | 50.0 | 250.0 |
| Cengkareng | Jakarta Barat | 6.0 | 130.0 |
| Kebon Jeruk | Jakarta Barat | 10.0 | 160.0 |
| Grogol Petamburan | Jakarta Barat | 8.0 | 140.0 |
| Matraman | Jakarta Timur | 9.0 | 145.0 |
| Jatinegara | Jakarta Timur | 7.0 | 135.0 |
| Cakung | Jakarta Timur | 5.0 | 115.0 |

#### Jawa Barat (10 kecamatan)
| Kecamatan | Kota | Elevasi (m) | Drainage Capacity |
|---|---|---|---|
| Bandung Wetan | Kota Bandung | 768.0 | 220.0 |
| Cicendo | Kota Bandung | 750.0 | 210.0 |
| Coblong | Kota Bandung | 800.0 | 240.0 |
| Bogor Tengah | Kota Bogor | 290.0 | 190.0 |
| Bogor Utara | Kota Bogor | 250.0 | 180.0 |
| Tanah Sareal | Kota Bogor | 270.0 | 185.0 |
| Bekasi Timur | Kota Bekasi | 19.0 | 125.0 |
| Bekasi Barat | Kota Bekasi | 15.0 | 120.0 |
| Pondok Gede | Kota Bekasi | 22.0 | 130.0 |
| Depok | Kota Depok | 80.0 | 165.0 |

### Data Historis Banjir
- **Total kejadian:** 646 flood events
- **Rentang waktu:** 2 tahun terakhir dari tanggal seeding
- **Musim hujan (data lebih padat):** November, Desember, Januari, Februari, Maret
- **Wilayah rawan:** elevasi < 20 m DAN drainage capacity < 150
- **Probabilitas flood event per hari (musim hujan):** 20% per wilayah rawan
- **Skala keparahan:** 1-4

### Data Jalan (OpenStreetMap)
- **Total ruas jalan:** 27.835
- **Sumber:** OpenStreetMap via Overpass API
- **File raw:** `data/raw/osm/roads.csv`
- **Tipe jalan:** primary, secondary, tertiary, residential

### Data Fasilitas Publik (OpenStreetMap)
- **Total fasilitas:** 11.233
- **Tipe:** hospital, clinic, school, government
- **Sumber:** OpenStreetMap
- **File raw:** `data/raw/osm/fasilitas_kesehatan.csv`, `data/raw/osm/fasilitas_publik.csv`

### Data Cuaca BMKG
- **Total record:** 432
- **Sumber:** BMKG Prakiraan Cuaca
- **File raw:** `data/raw/bmkg/prakiraan_cuaca.csv`

### Risk Scores
- **Titik historis per wilayah:** 23 jam lalu + 1 entry terkini = 24 titik data
- **Total titik historis:** 25 wilayah x 23 = 575 titik historis + 25 entry terkini = 600 record
- **Pola variasi tren:** mengikuti siklus harian (puncak siang WIB), time_factor = sin(pi * jam/18) * 0.12
- **Noise per titik:** random -8% hingga +8%

### Rekomendasi Tindakan
- **Total rekomendasi unik:** 39
- **Template per kategori:**
  - KRITIS (URS 76-100): 3 template (evakuasi, hindari perjalanan, posko darurat)
  - TINGGI (URS 51-75): 3 template (waspada banjir, rute alternatif, fasilitas kesehatan)
  - SEDANG (URS 26-50): 2 template (pantau cuaca, periksa kondisi jalan)
  - RENDAH (URS 0-25): 1 template (kondisi relatif aman)
- **Level urgensi:** Segera, Waspada, Siaga
- **Tipe:** alert, route, service

### Penjaringan — Wilayah KRITIS (Demo)
Penjaringan, Jakarta Utara di-set manual sebagai KRITIS dengan URS 84.2. Dipilih karena secara geografis memang rawan banjir: elevasi 2 m (terendah dari semua wilayah), drainage capacity 80 (terkecil dari semua wilayah).

### Akun Pengguna (2 akun)
| Username | Role | Password |
|---|---|---|
| admin | government | Admin123! |
| public | public | Admin123! |

---

## 7. Backend — FastAPI

### Struktur Direktori
```
src/uris_ai/
├── api/
│   ├── main.py              # App factory, middleware, endpoint utama
│   ├── dependencies.py      # DI: get_db, get_current_user, require_role
│   ├── middleware.py        # RateLimit, RequestLogging, HTTPSRedirect
│   ├── schemas.py           # Pydantic request/response schemas
│   └── routers/
│       ├── auth.py              # POST /auth/login, POST /auth/logout
│       ├── risk.py              # GET /regions/risk, /{id}/risk, /{id}/risk/trend
│       ├── recommendations.py   # GET /regions/{id}/recommendations, POST /routes/safe
│       └── users.py             # GET /users/me
├── models/
│   ├── database.py          # SQLAlchemy ORM models (8 tabel)
│   └── db_utils.py          # Engine factory PyMySQL + SSL
├── ml/
│   ├── flood_risk_engine.py         # Klasifikasi kategori risiko
│   ├── risk_scoring_engine.py       # Kalkulasi URS dan tren
│   └── recommendation_engine.py    # Rekomendasi dan rute aman
├── services/
│   ├── auth_service.py      # JWT create/decode, bcrypt verify
│   └── cache_service.py     # Redis cache wrapper (opsional)
├── security/
│   └── input_validation.py  # InputValidator
├── database/
│   └── optimization.py      # DB index management
├── utils/
│   ├── logging_config.py    # Setup logging
│   └── monitoring.py        # Application Insights wrapper
├── config.py                # Settings dari .env (pydantic-settings)
└── startup.py               # Startup: buat index, cache warming
```

### Semua API Endpoints

#### System
| Method | Path | Auth | Keterangan |
|---|---|---|---|
| GET | `/` | — | Info aplikasi: name, version, status |
| GET | `/health` | — | Health check dasar |
| GET | `/health/ready` | — | Readiness: cek DB + cache |
| GET | `/health/live` | — | Liveness: proses masih berjalan |
| GET | `/health/performance` | — | Status index DB + cache |
| GET | `/api/dashboard` | — | Regions + KPI summary + maps_key |

#### Authentication
| Method | Path | Auth | Keterangan |
|---|---|---|---|
| POST | `/auth/login` | — | Form-data login, return JWT |
| POST | `/auth/logout` | Bearer | Logout (client-side invalidation) |

Login request format: `application/x-www-form-urlencoded`
Fields: `username`, `password`

Login response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800,
  "role": "government"
}
```

#### Risk
| Method | Path | Auth | Query Params | Keterangan |
|---|---|---|---|---|
| GET | `/regions/risk` | — | — | URS semua wilayah |
| GET | `/regions/{id}/risk` | — | — | URS satu wilayah |
| GET | `/regions/{id}/risk/trend` | — | `hours` (1-168, default 24) | Tren URS |

#### Recommendations & Routes
| Method | Path | Auth | Keterangan |
|---|---|---|---|
| GET | `/regions/{id}/recommendations` | — | Rekomendasi aktif per wilayah |
| POST | `/routes/safe` | — | Cari rute aman dari origin ke destination |

#### Users
| Method | Path | Auth | Keterangan |
|---|---|---|---|
| GET | `/users/me` | Bearer | Info pengguna yang sedang login |

**Catatan:** Seluruh endpoint data (risk, recommendations, routes) bersifat PUBLIK — tidak memerlukan token.

### Middleware (urutan penerapan)
| Middleware | Config Default |
|---|---|
| HTTPSRedirectMiddleware | Dinonaktifkan di dev (`enforce_https=False`) |
| CORSMiddleware | `allow_origins=["*"]`, semua method dan header |
| RequestLoggingMiddleware | Log semua request: method, path, status, durasi ms |
| RateLimitMiddleware | Default 60 req/menit, 1000 req/jam per IP |

Rate limit khusus per endpoint:
- `/auth/login`: 10 req/menit, 100 req/jam
- `/routes/safe`: 30 req/menit, 500 req/jam
- `/health/*`: dikecualikan dari rate limiting

### Response `GET /api/dashboard`
```json
{
  "summary": {
    "total_regions": 25,
    "kritis_count": 1,
    "avg_urs": 42.3
  },
  "regions": [...],
  "maps_key": "...",
  "updated_at": "2026-06-03T..."
}
```

---

## 8. Frontend — React

### Struktur File
```
frontend/
├── index.html
├── package.json             # version 0.1.0
├── vite.config.js           # Dev proxy ke :8000, build ke src/uris_ai/static/
├── tailwind.config.js       # Custom theme Ocean Deep
├── postcss.config.js
└── src/
    ├── main.jsx             # Entry: BrowserRouter + QueryClientProvider
    ├── App.jsx              # Dashboard utama (/dashboard)
    ├── api.js               # fetch wrapper ke backend endpoints
    ├── store.js             # Zustand global state
    ├── utils.js             # getRiskColor, filterRegions, CITIES, formatURS
    ├── index.css            # Global styles, .card, .btn-accent, .risk-badge, .live-dot
    ├── components/
    │   ├── Header.jsx
    │   ├── KpiCards.jsx
    │   ├── Map.jsx
    │   ├── Sidebar.jsx
    │   ├── DetailPanel.jsx
    │   ├── DisclaimerModal.jsx
    │   └── LoadingScreen.jsx
    └── pages/
        └── LandingPage.jsx
```

### Routes
```
/            -> LandingPage
/dashboard   -> App (dashboard utama)
```

### Zustand Store (`store.js`)
| State | Tipe | Default | Keterangan |
|---|---|---|---|
| selectedRegionId | number or null | null | Wilayah yang dipilih |
| cityFilter | string | "Semua" | Filter kota aktif |
| search | string | "" | Query pencarian |
| disclaimerDone | boolean | dari sessionStorage | Status disclaimer |

### React Query Keys
| Query Key | Endpoint | Keterangan |
|---|---|---|
| `["dashboard"]` | GET /api/dashboard | Data semua wilayah + KPI |
| `["trend", regionId]` | GET /regions/{id}/risk/trend?hours=24 | Tren 24 jam |
| `["recs", regionId]` | GET /regions/{id}/recommendations | Rekomendasi aktif |

### API Functions (`api.js`)
```javascript
api.dashboard()                    // GET /api/dashboard
api.regionRisk(id)                 // GET /regions/{id}/risk
api.recommendations(id)            // GET /regions/{id}/recommendations
api.riskTrend(id, hours=24)        // GET /regions/{id}/risk/trend?hours=24
api.safeRoute(origin, dest)        // POST /routes/safe
```

### Tema Visual — Ocean Deep (tailwind.config.js)
| Token | Hex | Keterangan |
|---|---|---|
| b0 | #0a1628 | Background utama |
| b1 | #0f2040 | Panel / sidebar |
| b2 | #162d50 | Card |
| b2h | #1e3a63 | Card hover |
| bd | #1a3a5c 50 | Border |
| ba | #3a6a8c | Border aktif |
| t1 | #e2f0f9 | Teks utama |
| t2 | #7ab8d9 | Teks sekunder |
| t3 | #3a6a8c | Teks muted |
| accent | #00b4d8 | Warna aksen |
| accent-h | #0096c7 | Aksen hover |

Custom breakpoint tambahan: `xs: 480px`

### Warna Risiko
| Kategori | URS | Hex |
|---|---|---|
| RENDAH | 0-25 | #2dc653 |
| SEDANG | 26-50 | #f4a621 |
| TINGGI | 51-75 | #f25c54 |
| KRITIS | 76-100 | #b44fd4 |

### Filter Kota
Array `CITIES = ["Semua", "Jakarta", "Bandung", "Bogor", "Bekasi", "Depok"]`

Logic filter `filterRegions()`: cocokkan nilai `kota` atau `region_name` dengan filter menggunakan `String.includes()` case-insensitive. Pilih "Jakarta" menampilkan semua wilayah yang kota-nya mengandung "jakarta".

### Dev Server
- Port: 5173
- Proxy ke `http://127.0.0.1:8000`: `/api/*`, `/regions/*`, `/auth/*`, `/health/*`, `/routes/*`

### Build Produksi
```
npm run build
// Output: src/uris_ai/static/
// Diakses via FastAPI StaticFiles di /assets/*
```

### Perintah Windows (Laragon)
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
$env:PATH = "C:\laragon\bin\nodejs\node-v23.3.0-win-x64;" + $env:PATH
cd frontend
npm install
node_modules\.bin\vite.cmd      # dev server
node_modules\.bin\vite.cmd build  # produksi
```

---

## 9. Machine Learning

### Model Files
| File | Keterangan |
|---|---|
| `models/flood_risk_model.pkl` | Model scikit-learn terlatih |
| `models/flood_risk_scaler.pkl` | Scaler untuk normalisasi fitur |
| `models/flood_risk_metadata.json` | Metadata model (versi, fitur, threshold) |

### FloodRiskEngine (`src/uris_ai/ml/flood_risk_engine.py`)
- Mengklasifikasikan nilai URS ke 4 kategori risiko
- Threshold: 0-25 RENDAH, 26-50 SEDANG, 51-75 TINGGI, 76-100 KRITIS
- Digunakan di `/api/dashboard` dan router `/regions/risk`

### RiskScoringEngine (`src/uris_ai/ml/risk_scoring_engine.py`)
- Formula URS: `(flood_risk x 0.50) + (traffic_impact x 0.30) + (service_access x 0.20)`
- Method `get_risk_trend(region_id, hours)`: ambil titik historis dari tabel `risk_scores`

### RecommendationEngine (`src/uris_ai/ml/recommendation_engine.py`)
- Menentukan rekomendasi berdasarkan kategori risiko wilayah
- Method `find_safe_route(origin, destination)`: menghindari wilayah TINGGI dan KRITIS

### Training Script
`scripts/train_flood_model.py` — melatih ulang model dari data historis

---

## 10. Autentikasi & Otorisasi

### Mekanisme JWT
- **Algoritma:** HS256
- **Library:** `python-jose[cryptography]` + `passlib[bcrypt]`
- **Expire:** 1800 detik (30 menit)
- **Login format:** `application/x-www-form-urlencoded` (OAuth2PasswordRequestForm)

### Roles
| Role | Keterangan |
|---|---|
| `government` | Pengguna pemerintah (akun: admin) |
| `public` | Pengguna umum (akun: public) |

### Status Otorisasi Saat Ini
`require_role()` tersedia di `dependencies.py` tapi **belum diterapkan ke endpoint manapun**.

- Semua endpoint data (`/regions/*`, `/routes/*`) dapat diakses tanpa token
- Token hanya diperlukan untuk: `POST /auth/logout` dan `GET /users/me`

### Perbedaan Fungsional Government vs Public (saat ini)
Tidak ada perbedaan akses data antara kedua role. Perbedaan hanya:
- Field `role` tersimpan di database
- Field `role` dikembalikan dalam response login

### Rencana ke Depan
- Role `government` mendapatkan akses endpoint admin
- Manajemen multi-user pemerintah
- Endpoint data sensitif dibatasi hanya untuk `government`
- UI login di frontend (saat ini belum ada)

### Alur Login
```
POST /auth/login
  Body (form-data): username=admin&password=Admin123!
  Response 200: { access_token, token_type: "bearer", expires_in: 1800, role: "government" }

GET /users/me
  Header: Authorization: Bearer <token>
  Response 200: { id, username, email, role, is_active, ... }
```

---

## 11. Urban Risk Score (URS)

### Formula
```
URS = (flood_risk x 0.50) + (traffic_impact x 0.30) + (service_access x 0.20)
```

### Komponen Score
| Komponen | Bobot | Dasar Kalkulasi (Simulasi) |
|---|---|---|
| flood_risk | 50% | `max(0, (20 - elevasi) x 3 + (150 - drainage) x 0.3) + noise` |
| traffic_impact | 30% | `flood_risk x 0.7 + noise(-5, +15)` |
| service_access | 20% | `flood_risk x 0.5 + noise(-10, +20)` |

### Kategori dan Warna
| Kategori | Rentang | Warna |
|---|---|---|
| RENDAH | 0-25 | #2dc653 (hijau) |
| SEDANG | 26-50 | #f4a621 (oranye) |
| TINGGI | 51-75 | #f25c54 (merah) |
| KRITIS | 76-100 | #b44fd4 (ungu) |

### Nilai URS Demo
- **Penjaringan:** 84.2 — KRITIS (set manual; elevasi 2m, drainage 80)
- **Wilayah Jakarta Utara lainnya (Kelapa Gading, Pademangan):** TINGGI
- **Wilayah Bandung, Bogor, Depok:** RENDAH (elevasi tinggi)
- **Rata-rata seluruh wilayah:** sekitar 42 (SEDANG)

### Tren Historis
- 24 titik data per wilayah (1 titik per jam)
- 23 jam historis + 1 entry terkini = 24 total
- Variasi: pola sinusoidal harian (puncak siang WIB) + noise -8% hingga +8%

---

## 12. Komponen Dashboard

### Header (`Header.jsx`)
- **Tinggi:** 52px mobile / 64px desktop
- **Logo desktop:** `logowhite_nobg.png`, `h-12 max-w-[160px]` — hanya `sm+`
- **Logo mobile:** `logowhite_single.png`, `h-9 w-9` — hanya `< sm`
- **Klik logo:** link ke `/` (LandingPage)
- **Badge LIVE:** hijau `#2dc653`, animasi pulse, tampil di `xs+`
- **Timestamp:** jam dan tanggal dalam 2 kotak terpisah, font mono `11px`, tampil `sm+`
- **Warna header:** gradient dari `b1` ke `b2`

### KpiCards (`KpiCards.jsx`)
3 kartu ringkasan:
1. Wilayah Kritis — jumlah wilayah dengan kategori KRITIS
2. Rata-rata URS — rata-rata urban_risk_score semua wilayah
3. Wilayah Dipantau — total wilayah (25)

### Map (`Map.jsx`)
- **Provider:** Azure Maps SDK (`atlas`), style `night`
- **Center default:** `[106.8456, -6.2088]`
- **Zoom default:** 10
- **Markers:** BubbleLayer, radius 14px, warna sesuai kategori, label angka URS putih `10px`
- **Flood overlay:** BubbleLayer terpisah; TINGGI radius 28px, KRITIS radius 36px, opacity 0.14
- **Legend:** pojok kiri bawah, `bottom-10 left-3`, z-index 10
- **Fly-to:** zoom 13, animasi `ease` durasi 600ms saat wilayah dipilih
- **Pattern anti-race-condition:** `regionsRef.current` selalu menyimpan data terbaru
- **Click event:** pada bubble layer, ambil `props.id` lalu `setSelectedRegion(id)`

### Sidebar (`Sidebar.jsx`)
- **Lebar desktop:** 300px (`flex-shrink-0`)
- **Komponen terpisah:** `SidebarFilters` (chip + search) dan `SidebarList` (daftar scrollable)
- **Filter chips:** Semua, Jakarta, Bandung, Bogor, Bekasi, Depok
- **Urutan daftar:** descending by `urban_risk_score`
- **RegionCard:** rank (index+1), nama, kota, badge kategori, URS angka + progress bar
- **Mobile:** tidak tampil langsung; diakses via drawer

### DetailPanel (`DetailPanel.jsx`)
- **Desktop:** `w-[320px] flex-shrink-0`, border kiri
- **Mobile (fullscreen prop):** `h-full w-full`, dirender dalam `fixed inset-0 z-50` di App.jsx
- **Scrollable area:** `flex-1 overflow-y-auto min-h-0`
- **URS Gauge:** angka `42px font-extrabold` + progress bar penuh (0-100)
- **3 StatBars:**
  - Risiko Banjir — warna `#f25c54`
  - Dampak Lalu Lintas — warna `#f4a621`
  - Aksesibilitas — warna `#2dc653`
- **TrendChart:** Recharts AreaChart, height 60px, dataKey `urban_risk_score`, stroke `#00b4d8`
- **Rekomendasi:** max 6 item, tampil dari index 0-5

### Ikon Rekomendasi (gambar custom di `public/`)
| Tipe | File | Label |
|---|---|---|
| alert | /allert.png | Peringatan |
| route | /rute.png | Rute |
| service | /fasilitas.png | Fasilitas |
| evacuation | /allert.png | Evakuasi |
| resource_allocation | /fasilitas.png | Sumber Daya |

### UrgencyBadge
| Level | Warna Border/Text |
|---|---|
| Segera | #b44fd4 (ungu) |
| Waspada | #f25c54 (merah) |
| Siaga | #f4a621 (oranye) |

### DisclaimerModal (`DisclaimerModal.jsx`)
- Tampil saat `disclaimerDone === false`
- Persistensi: `sessionStorage.setItem("urisai_disclaimer_ok", "1")`
- Reset setiap tutup/buka browser baru

### LoadingScreen (`LoadingScreen.jsx`)
- `done` prop dari `isSuccess` React Query dashboard
- Animasi step-by-step saat data dimuat

### Layout Responsif (`App.jsx`)
```
Desktop (lg+):
  [Map flex-1] [Sidebar 300px] [DetailPanel 320px]

Mobile (<lg):
  [Map fullscreen]
  [Tombol "Wilayah" top-right]
    -> Drawer bawah max-h-[85vh] (mobile)
    -> Panel kanan w-[320px] (tablet sm+)
  [Detail: fixed inset-0 z-50 height:100dvh]
```

Root App: `div.flex.flex-col.h-screen.overflow-hidden`

### LandingPage (`LandingPage.jsx`)
- **Navbar:** `bg-white`, sticky, z-50, shadow-sm, border-b gray-100
- **Logo navbar desktop:** `logo.png`, `h-20`, tampil `sm+`
- **Logo navbar mobile:** `logo_single.png`, `h-10`, tampil `< sm`
- **Hero:** gradient teks accent, badge "Data Simulasi", 2 CTA button
- **Stats (4 item):** 25 Wilayah Dipantau, 27.835 Ruas Jalan, 11.233 Fasilitas Publik, 432 Data Cuaca BMKG
- **Fitur:** 6 cards (grid 1/2/3 kolom)
- **GitHub:** `https://github.com/rathaavle/uris-ai`
- **Footer:** "© 2026 URIS-AI · Data Simulasi untuk Keperluan Demo"

---

## 13. Scripts Utilitas

| Script | Keterangan |
|---|---|
| seed_data.py | Seed 25 wilayah, 646 flood events, roads (sampel), facilities (sampel) |
| import_raw_data.py | Import data dari CSV raw ke tabel database |
| collect_raw_data.py | Kumpulkan data dari BMKG dan sumber eksternal |
| collect_osm_roads.py | Kumpulkan 27.835 ruas jalan dari OpenStreetMap |
| retry_osm.py | Retry pengambilan data OSM yang gagal |
| generate_risk_scores.py | Buat risk score awal (rule-based simulasi per wilayah) |
| recalculate_risk_scores.py | Kalkulasi ulang semua risk score |
| generate_recommendations.py | Buat 39 rekomendasi berdasarkan kategori URS |
| generate_urs_history.py | Generate 23 titik historis per wilayah (tren 24 jam) |
| train_flood_model.py | Latih model ML flood risk, simpan ke models/ |
| create_admin.py | Buat akun admin baru |
| reset_passwords.py | Reset password pengguna |
| migrate_data.py | Migrasi data antar versi skema |
| test_connection.py | Test koneksi ke Azure MySQL |
| run_local.ps1 | Jalankan backend + frontend secara lokal (Windows) |
| setup_azure_windows.ps1 | Provisioning resource Azure dari Windows |
| setup_azure.sh | Provisioning resource Azure dari Linux/Mac |
| blue_green_deploy.sh | Blue-green deployment ke Azure |
| rollback_deployment.sh | Rollback ke versi deployment sebelumnya |
| run_smoke_tests.sh | Jalankan smoke test setelah deploy |

---

## 14. Konfigurasi & Environment

### Variabel .env Kunci

| Variabel | Nilai/Contoh | Keterangan |
|---|---|---|
| AZURE_MYSQL_CONNECTION_STRING | mysql+pymysql://mysqladmin:...@urisai-mysql.mysql.database.azure.com/uris-ai-db | Koneksi DB |
| AZURE_MAPS_KEY | (dari Azure portal) | Subscription key Azure Maps |
| AZURE_KEY_VAULT_URL | https://urisai-kv.vault.azure.net/ | URL Key Vault |
| AZURE_KEY_VAULT_ENABLED | false | Nonaktif di dev |
| SECRET_KEY | (random string) | JWT signing key |
| ALGORITHM | HS256 | JWT algoritma |
| ACCESS_TOKEN_EXPIRE_MINUTES | 30 | Expire JWT |
| APP_NAME | URIS-AI | Nama aplikasi |
| APP_VERSION | 0.1.0 | Versi aplikasi |
| APP_ENV | development | Environment |
| DEBUG | true | Mode debug |
| LOG_LEVEL | INFO | Level logging |
| API_HOST | 0.0.0.0 | Host binding |
| API_PORT | 8000 | Port API |
| API_RELOAD | true | Hot reload dev |
| ENABLE_RATE_LIMITING | true | Aktifkan rate limit |
| RATE_LIMIT_PER_MINUTE | 60 | Default per menit per IP |
| RATE_LIMIT_PER_HOUR | 1000 | Default per jam per IP |
| REDIS_URL | redis://localhost:6379 | Cache (opsional) |

### Terraform Variables
| Variable | Default | Keterangan |
|---|---|---|
| resource_group_name | uris-ai-rg | Nama resource group |
| location | southeastasia | Region Azure |
| environment | dev | dev/staging/production |
| enable_blue_green | false | Blue-green deployment slots |
| sql_admin_username | sqladmin | Username admin DB |

### Log Startup Normal
Startup berhasil menampilkan:
- Application startup: Initializing performance optimizations
- Cache service not available, skipping cache warming (normal tanpa Redis)
- Application startup completed successfully

---

## 15. Status Fitur

| Fitur | Status | Keterangan |
|---|---|---|
| Dashboard peta interaktif | Selesai | Azure Maps night style, bubble markers, flood overlay |
| Urban Risk Score 25 wilayah | Selesai | Simulasi, tren 24 jam tersedia |
| Filter wilayah per kota | Selesai | 6 filter: Semua/Jakarta/Bandung/Bogor/Bekasi/Depok |
| Rekomendasi tindakan | Selesai | 39 rekomendasi unik, ikon gambar custom |
| Detail panel (URS + stat + tren) | Selesai | Desktop 320px + mobile fullscreen |
| Tren URS 24 jam (Recharts) | Selesai | AreaChart dengan 24 titik data |
| Responsive mobile | Selesai | Bottom drawer + fullscreen overlay detail |
| LandingPage | Selesai | Navbar putih, hero, stats, 6 fitur, CTA |
| Disclaimer modal | Selesai | sessionStorage, satu kali per sesi |
| Loading screen | Selesai | Step-by-step animasi |
| API publik tanpa auth | Selesai | Risk, recommendations, routes dapat diakses bebas |
| Login JWT (backend) | Selesai | Endpoint POST /auth/login berfungsi |
| Role-based access control | Sebagian | require_role() ada, belum diterapkan ke endpoint |
| Frontend login UI | Belum | Tidak ada form login di frontend |
| Token storage frontend | Belum | Token tidak disimpan di sisi klien |
| Safe route UI | Belum | API POST /routes/safe ada, UI belum dibuat |
| Auto-refresh interval | Belum dikonfirmasi | React Query refetchInterval belum diverifikasi aktif |
| Redis cache | Opsional | Berjalan tanpa Redis, fallback ke DB langsung |
| Application Insights | Opsional | Dinonaktifkan di dev, aktif jika APPINSIGHTS_CONNECTION_STRING diset |

---

## 16. Cara Menjalankan Lokal

### Prerequisites
- Python 3.11+
- Node.js (diuji dengan v23.3.0 via Laragon)
- Koneksi internet ke Azure MySQL

### Backend

Jalankan di PowerShell dari direktori root D:\\project\\uris-ai:

  Set PYTHONPATH = src
  python -m uvicorn uris_ai.api.main:app --reload --host 0.0.0.0 --port 8000

Tersedia di:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Frontend

  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
  Set PATH = C:\\laragon\\bin\\nodejs\\node-v23.3.0-win-x64;%PATH%
  cd frontend
  npm install
  node_modules\\.bin\\vite.cmd

Dev server: http://localhost:5173

### Build Produksi

  cd frontend
  node_modules\\.bin\\vite.cmd build
  Output: src\\uris_ai\\static\\

### Seed Data (database kosong)

  python scripts/seed_data.py
  python scripts/import_raw_data.py
  python scripts/generate_risk_scores.py
  python scripts/recalculate_risk_scores.py
  python scripts/generate_urs_history.py
  python scripts/generate_recommendations.py

---

*Dokumentasi ini mencerminkan kondisi aktual proyek pada Juni 2026.*
*Status: Demo / Development — data URS bersifat simulasi.*
