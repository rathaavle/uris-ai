# URIS-AI — Analisis Data & Status Sistem

> Dokumen ini menjelaskan status sistem URIS-AI secara lengkap: stack teknologi, komponen frontend, perbedaan role, status data, dan gap yang masih ada.

---

## 1. Stack Teknologi (Status Sekarang)

### Backend

- **FastAPI 0.109.2** + **Uvicorn** — ASGI server, port 8000
- **SQLAlchemy 2.0** + **PyMySQL 1.1.0** — ORM + driver MySQL (tanpa ODBC)
- **Azure Database for MySQL** (Free Tier B1MS) — `urisai-mysql.mysql.database.azure.com`
- **python-jose** + **passlib[bcrypt]** — autentikasi JWT

### Frontend

- **React 18.3.1** + **Vite 5.3.1** — build tool + dev server (port 5173)
- **TailwindCSS 3.4.4** — utility-first CSS, tema Ocean Deep
- **@tanstack/react-query 5.40.0** — server state + auto-refresh 15 menit
- **Zustand 4.5.2** — client state (selectedRegion, filter, search)
- **azure-maps-control 3.3.0** — peta interaktif Azure Maps night style
- **Recharts 2.12.7** — chart tren URS (AreaChart)
- **React Router DOM 6.23.1** — routing SPA (`/` → LandingPage, `/dashboard` → App)

> **Catatan:** Frontend sebelumnya berbasis vanilla HTML/CSS/JS, sudah sepenuhnya diganti React 18 + Vite.

### Infrastruktur Azure (Aktif)

| Layanan                  | Resource                        | Region        |
| ------------------------ | ------------------------------- | ------------- |
| Azure Database for MySQL | `urisai-mysql` (Free Tier B1MS) | southeastasia |
| Azure Blob Storage       | `urisaistorage`                 | southeastasia |
| Azure Key Vault          | `urisai-kv`                     | southeastasia |
| Azure Maps               | `urisai-maps` (Gen2)            | eastus        |

---

## 2. Komponen Frontend

### Routing

```
/            → LandingPage.jsx
/dashboard   → App.jsx (dashboard utama)
```

### Komponen Dashboard (`/dashboard`)

| Komponen        | File                             | Fungsi                                                    |
| --------------- | -------------------------------- | --------------------------------------------------------- |
| App             | `App.jsx`                        | Root dashboard, layout responsif, drawer mobile           |
| Header          | `components/Header.jsx`          | Logo, badge LIVE, timestamp jam + tanggal                 |
| KpiCards        | `components/KpiCards.jsx`        | 3 kartu KPI: Wilayah Kritis, Rata-rata URS, Total Wilayah |
| Map             | `components/Map.jsx`             | Azure Maps, bubble layer, flood overlay, legend risiko    |
| Sidebar         | `components/Sidebar.jsx`         | Filter kota, search, daftar wilayah dengan URS bar        |
| DetailPanel     | `components/DetailPanel.jsx`     | URS gauge, stat bars, tren chart 24h, rekomendasi         |
| DisclaimerModal | `components/DisclaimerModal.jsx` | Modal "data simulasi", simpan ke sessionStorage           |
| LoadingScreen   | `components/LoadingScreen.jsx`   | Layar loading step-by-step saat data belum tersedia       |

### Komponen Landing Page (`/`)

| Komponen      | Keterangan                                                       |
| ------------- | ---------------------------------------------------------------- |
| Navbar        | Sticky, logo berwarna (logo.png desktop, logo_single.png mobile) |
| Hero          | Badge simulasi, headline gradient, CTA "Buka Dashboard" + GitHub |
| Stats Strip   | 25 Wilayah, 27.835 Jalan, 11.233 Fasilitas, 432 Data Cuaca       |
| Feature Cards | 6 fitur utama dengan gambar ilustrasi dari `public/`             |
| How It Works  | 3 langkah: Kumpul Data → Analisis AI → Visualisasi               |
| CTA Section   | Card dengan tombol "Buka Dashboard Sekarang →"                   |
| Footer        | © 2026 URIS-AI                                                   |

### Logo Usage

| Konteks                | File                   |
| ---------------------- | ---------------------- |
| Dashboard desktop      | `logowhite_nobg.png`   |
| Dashboard mobile       | `logowhite_single.png` |
| Landing navbar desktop | `logo.png`             |
| Landing navbar mobile  | `logo_single.png`      |

### Ikon Rekomendasi (custom images di `public/`)

| Tipe                         | File             |
| ---------------------------- | ---------------- |
| alert, evacuation            | `/allert.png`    |
| route                        | `/rute.png`      |
| service, resource_allocation | `/fasilitas.png` |

---

## 3. Fitur Government vs Public — Beda Nya Apa?

### Status Sekarang: Tidak Ada Perbedaan Fungsional

Ini yang penting untuk dipahami: **saat ini role `government` dan `public` tidak memiliki perbedaan akses apapun di level API maupun UI.**

#### Di Database

- Kolom `users.role` menyimpan nilai `'government'` atau `'public'`
- 2 akun tersedia: `admin` (government), `public` (public)

#### Di Backend

- Fungsi `require_role()` sudah ada di `dependencies.py`
- Tapi **belum diterapkan ke endpoint manapun**
- Semua endpoint `/regions/*`, `/routes/*`, `/api/dashboard` bisa diakses **tanpa token sama sekali**
- Token hanya diperlukan untuk: `POST /auth/logout` dan `GET /users/me`

#### Di Frontend

- **Tidak ada halaman login**
- **Tidak ada UI berbeda** untuk kedua role
- Dashboard bisa dibuka langsung tanpa login apapun

#### Satu-satunya Perbedaan Sekarang

Saat login via `POST /auth/login`, response mengembalikan `"role": "government"` atau `"role": "public"`. Itu saja — tidak digunakan untuk apapun lebih lanjut di sistem saat ini.

---

### Rencana Perbedaan ke Depan (Belum Diimplementasi)

| Fitur                        | public           | government        |
| ---------------------------- | ---------------- | ----------------- |
| Lihat dashboard risiko       | ✅               | ✅                |
| Lihat rekomendasi tindakan   | ✅               | ✅                |
| Cari rute aman               | ✅               | ✅                |
| Login                        | ❌ (tidak perlu) | ✅                |
| Notifikasi darurat push      | ❌               | ✅ (direncanakan) |
| Alokasi sumber daya darurat  | ❌               | ✅ (direncanakan) |
| Laporan teknis lengkap (PDF) | ❌               | ✅ (direncanakan) |
| Manajemen wilayah & data     | ❌               | ✅ (direncanakan) |
| Akses endpoint admin         | ❌               | ✅ (direncanakan) |

> **Kesimpulan:** Role dibuat dari awal agar fleksibel ke depan, tapi belum ada implementasi nyata. Untuk demo ini, semua pengguna (dengan atau tanpa login) mendapatkan akses yang sama.

---

## 4. Status Data

### Wilayah

- **25 kecamatan** — 15 Jakarta, 10 Jawa Barat (Bandung, Bogor, Bekasi, Depok)
- Semua wilayah memiliki koordinat latitude/longitude

### Risk Scores

- **24 titik data per wilayah** — 23 jam historis + 1 entry terkini
- **Total:** 600 record di tabel `risk_scores`
- Pola tren: sinusoidal harian (puncak siang WIB) + noise ±8%

### Penjaringan KRITIS (Demo)

- URS = **84.2**, kategori **KRITIS** — di-set manual untuk demo
- Alasan logis: elevasi 2m (terendah), drainage capacity 80 (terkecil)
- Memiliki 5 rekomendasi darurat detail

### Rekomendasi

- **39 rekomendasi unik** aktif di database
- Guard dedup sudah ada di `scripts/generate_recommendations.py`
- Template per kategori: KRITIS (3), TINGGI (3), SEDANG (2), RENDAH (1)

### Sumber Data Raw

| Sumber                  | Jumlah             | File                                                   |
| ----------------------- | ------------------ | ------------------------------------------------------ |
| BMKG Cuaca              | 432 record         | `data/raw/bmkg/prakiraan_cuaca.csv`                    |
| OSM Roads               | 27.835 jalan       | `data/raw/osm/roads.csv`                               |
| OSM Fasilitas Kesehatan | bagian dari 11.233 | `data/raw/osm/fasilitas_kesehatan.csv`                 |
| OSM Fasilitas Publik    | bagian dari 11.233 | `data/raw/osm/fasilitas_publik.csv`                    |
| Historis Banjir         | 646 events         | `data/raw/historis_banjir/historis_banjir_jakarta.csv` |
| PetaBencana             | flood reports      | `data/raw/petabencana/flood_reports.csv`               |
| Wilayah Admin           | 25 wilayah         | `data/raw/wilayah/wilayah_administrasi.csv`            |

> **Semua data URS bersifat simulasi** — dihitung rule-based dari formula geografis + noise. Ini disengaja untuk keperluan demo dan presentasi.

---

## 5. Endpoint API Utama

### Dashboard (digunakan Frontend)

```
GET  /api/dashboard          → regions + KPI summary + maps_key (publik, tanpa auth)
GET  /regions/{id}/risk/trend?hours=24  → tren URS 24 jam
GET  /regions/{id}/recommendations      → rekomendasi aktif
POST /routes/safe            → rute aman (origin → destination, hindari TINGGI/KRITIS)
```

### Auth

```
POST /auth/login             → JWT token (form-data: username, password)
GET  /users/me               → info user (perlu Bearer token)
```

### Health

```
GET  /health                 → status dasar
GET  /health/ready           → cek DB + cache
```

---

## 6. Gap & Hal yang Belum Ada

| Fitur                                  | Status                              |
| -------------------------------------- | ----------------------------------- |
| Halaman login UI                       | ❌ Belum ada                        |
| UI perbedaan role government vs public | ❌ Belum ada                        |
| Safe route UI di frontend              | ❌ Belum ada (backend sudah ada)    |
| Data cuaca real-time (BMKG live)       | ❌ Simulasi                         |
| Notifikasi push darurat                | ❌ Belum ada                        |
| Upload laporan banjir manual           | ❌ Belum ada                        |
| Pagination daftar wilayah              | ❌ Belum diperlukan (25 wilayah)    |
| Unit tests frontend                    | ❌ Belum ada                        |
| CI/CD pipeline                         | ❌ Belum aktif                      |
| Deployment ke Azure (live URL)         | ❌ Belum (lihat rencana deployment) |

---

## 7. Cara Menjalankan Lokal

### Backend

```powershell
# Dari root project
cd D:\project\uris-ai
python -m uvicorn uris_ai.api.main:app --reload --host 0.0.0.0 --port 8000
# Atau lewat scripts:
# python -m uris_ai.api.main
```

### Frontend

```powershell
cd D:\project\uris-ai\frontend
node_modules\.bin\vite.cmd        # dev server → http://localhost:5173
node_modules\.bin\vite.cmd build  # build produksi → src/uris_ai/static/
```

> **Catatan Windows:** Gunakan `node_modules\.bin\vite.cmd` bukan `npm run dev` karena masalah PATH Node.js di environment ini.

### Backend harus jalan dulu

Jika backend belum jalan, frontend akan terus menampilkan loading screen (proxy ke `:8000` gagal connect).

---

## 8. Rencana Deployment Azure (Free Tier)

| Komponen               | Layanan Azure                 | Biaya                    |
| ---------------------- | ----------------------------- | ------------------------ |
| Frontend React (build) | Azure Static Web Apps         | Gratis                   |
| Backend FastAPI        | Azure App Service F1          | Gratis (60 CPU min/hari) |
| Database MySQL         | Azure Database for MySQL B1MS | Gratis (sudah aktif)     |

Langkah deployment:

1. Build frontend: `npm run build` → output ke `src/uris_ai/static/`
2. Buat Azure Static Web Apps resource
3. Configure App Service untuk FastAPI (Procfile / startup command)
4. Set environment variables di App Service
5. Update CORS di `main.py` untuk domain produksi
6. Update `vite.config.js` untuk URL API produksi

---

_Dokumen ini terakhir diperbarui: Juni 2026_
