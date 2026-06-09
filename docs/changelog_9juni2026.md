# Changelog — 9 Juni 2026

## Ringkasan

Sesi ini mencakup migrasi database dari Azure MySQL ke Neon PostgreSQL, perbaikan koordinat wilayah, pengisian data historis, dan penghapusan resource berbayar di Azure.

---

## 1. Investigasi Tagihan Azure

**Masalah:** Tagihan Azure sebesar -Rp22.680 ditemukan di kartu kredit.

**Temuan via Azure CLI:**

- `urisai-mysql` (MySQL Flexible Server B1ms) — penyebab utama, ~$15–20/bulan
- `urisai-plan` (App Service Basic B1 Linux) — tagihan bulan lalu, sudah tidak ada
- `urisai-maps` (Azure Maps G2) — per request
- `foodcheck-rg` — 3 Cognitive Services dari project lain yang masih aktif
- `urisaistorage`, `urisai-kv` — biaya sangat kecil

**Tindakan:** MySQL di-stop sementara untuk menghentikan tagihan compute.

```bash
az mysql flexible-server stop --resource-group uris-ai-rg --name urisai-mysql
```

---

## 2. Migrasi Database: Azure MySQL → Neon PostgreSQL

**Latar belakang:** MySQL Flexible Server tidak memiliki free tier — selalu ditagih selama aktif. Keputusan migrasi ke Neon PostgreSQL yang gratis permanen.

### Perubahan Kode

#### `requirements.txt`

- Hapus: `PyMySQL==1.1.0`
- Tambah: `psycopg2-binary==2.9.9`

#### `Dockerfile`

- Tambah `libpq-dev` di apt-get install (dependency psycopg2)

#### `src/uris_ai/models/db_utils.py`

- Hapus custom MySQL `_creator()` function dengan pymysql + SSL dict
- Ganti dengan engine PostgreSQL standard via `create_engine()` dengan `sslmode=require`
- Support auto-normalisasi `postgres://` → `postgresql+psycopg2://`
- Pool size disesuaikan untuk Neon connection pooling (pool_size=5, max_overflow=2)

#### `src/uris_ai/config.py`

- Tambah field `database_url` untuk PostgreSQL connection URL
- Tambah property `active_database_url` — prioritas `database_url`, fallback ke `azure_mysql_connection_string` untuk backward compatibility
- Field MySQL ditandai `[Deprecated]`

#### `src/uris_ai/api/dependencies.py`

- `get_engine()` sekarang pakai `settings.active_database_url`
- Tambah error message yang jelas jika tidak ada database URL

#### `src/uris_ai/database/optimization.py`

- Ganti `information_schema.statistics` (MySQL) → `pg_indexes` (PostgreSQL)
- Ganti `SET SHOWPLAN_TEXT ON` (SQL Server) → `EXPLAIN ANALYZE` (PostgreSQL)
- Ganti `sys.query_store_*` DMV (SQL Server) → `pg_stat_statements` (PostgreSQL)
- Ganti `sys.dm_db_index_usage_stats` → `pg_stat_user_indexes` (PostgreSQL)
- Ganti `UPDATE STATISTICS ... WITH FULLSCAN` → `ANALYZE table_name` (PostgreSQL)
- Ganti `SELECT TOP 20` → `SELECT ... LIMIT 20`

#### `src/uris_ai/models/schema.sql`

- Dokumentasi DDL (tidak dipakai langsung, SQLAlchemy auto-create)
- Catatan: syntax MySQL (`AUTO_INCREMENT`, `ON UPDATE CURRENT_TIMESTAMP`) masih ada di file ini sebagai referensi historis

### Scripts yang Diupdate

Semua script berikut diupdate dari `settings.azure_mysql_connection_string` → `settings.active_database_url`:

- `scripts/import_raw_data.py`
- `scripts/generate_risk_scores.py`
- `scripts/generate_urs_history.py`
- `scripts/generate_recommendations.py`
- `scripts/migrate_data.py`
- `scripts/create_admin.py`

#### `scripts/generate_urs_history.py`

- Fix query DELETE untuk PostgreSQL (hapus alias subquery yang tidak didukung)

### Setup Neon

- Provider: [neon.tech](https://neon.tech)
- Region: AWS Asia Pacific 1 (Singapore)
- PostgreSQL version: 17
- Plan: Free tier (0.5 GB storage, auto-suspend saat idle)
- Connection string di-set sebagai environment variable `DATABASE_URL` di Google Cloud Run

---

## 3. Rebuild & Redeploy ke Google Cloud Run

**Artifact Registry:** `asia-southeast1-docker.pkg.dev/uris-ai-project/urisai-repo/urisai-api:latest`

```bash
gcloud builds submit --tag asia-southeast1-docker.pkg.dev/uris-ai-project/urisai-repo/urisai-api:latest --region asia-southeast1 .
gcloud run services update urisai-api --region asia-southeast1 --image ...
```

Environment variable baru yang ditambahkan ke Cloud Run:

```
DATABASE_URL=postgresql://neondb_owner:***@ep-raspy-cell-aow5caaf.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

---

## 4. Pengisian Data ke Neon

Semua data di-generate ulang dari CSV dan script karena MySQL sudah tidak relevan.

| Tabel               | Sumber                                                | Jumlah                           |
| ------------------- | ----------------------------------------------------- | -------------------------------- |
| `regions`           | `wilayah_administrasi.csv`                            | 25 wilayah                       |
| `weather_data`      | `prakiraan_cuaca.csv` (BMKG)                          | 432 baris                        |
| `flood_events`      | Generated (synthetic, realistis)                      | 76 events                        |
| `public_facilities` | `fasilitas_publik.csv` (OSM)                          | 7.653 titik                      |
| `roads`             | `roads.csv` (OSM)                                     | 27.835 ruas                      |
| `risk_scores`       | `generate_risk_scores.py` + `generate_urs_history.py` | 600 points (24 jam × 25 wilayah) |
| `recommendations`   | `generate_recommendations.py`                         | 40 rekomendasi                   |
| `users`             | `create_admin.py`                                     | 2 users (admin, public)          |

**Flood events** di-generate secara synthetic karena CSV `historis_banjir_jakarta.csv` kosong (tidak ada data dari petabencana.id saat fetch). Data dibuat realistis berdasarkan wilayah rawan banjir Jakarta yang diketahui (Penjaringan severity 4, Jatinegara severity 3, dst).

---

## 5. Perbaikan Koordinat Wilayah

**Masalah:** Koordinat wilayah di database tidak akurat — Bogor Utara dan Tanah Sareal hampir sama posisinya sehingga bubble di peta overlap dan klik wilayah tidak sesuai.

**Solusi:** Update koordinat ke titik tengah kecamatan yang akurat berdasarkan posisi geografis nyata.

Wilayah dengan perubahan signifikan:

| Wilayah       | Koordinat Lama    | Koordinat Baru    |
| ------------- | ----------------- | ----------------- |
| Bogor Utara   | -6.5700, 106.8000 | -6.5556, 106.8089 |
| Tanah Sareal  | -6.5833, 106.7833 | -6.5703, 106.7706 |
| Bogor Tengah  | -6.5950, 106.7969 | -6.5961, 106.7978 |
| Kemayoran     | -6.1667, 106.8500 | -6.1572, 106.8603 |
| Penjaringan   | -6.1167, 106.7833 | -6.1089, 106.7822 |
| Cengkareng    | -6.1500, 106.7333 | -6.1461, 106.7344 |
| Kebon Jeruk   | -6.1833, 106.7667 | -6.1911, 106.7611 |
| Tebet         | -6.2333, 106.8500 | -6.2244, 106.8553 |
| Matraman      | -6.2000, 106.8667 | -6.2100, 106.8711 |
| Jatinegara    | -6.2167, 106.8667 | -6.2183, 106.8814 |
| Cakung        | -6.1667, 106.9333 | -6.1656, 106.9531 |
| Bandung Wetan | -6.9175, 107.6191 | -6.9022, 107.6333 |
| Bekasi Barat  | -6.2333, 106.9833 | -6.2469, 106.9658 |
| Depok         | -6.4000, 106.8186 | -6.4025, 106.7942 |

Update dilakukan langsung ke database Neon dan ke file `data/raw/wilayah/wilayah_administrasi.csv`.

---

## 6. Penghapusan Azure MySQL

Setelah semua data berhasil di-generate ke Neon dan app berjalan normal:

```bash
az mysql flexible-server delete --resource-group uris-ai-rg --name urisai-mysql --yes
```

**Status:** Dihapus permanen ✅ — tidak bisa di-undo.

---

## 7. Ringkasan Status Akhir

### Resource Azure yang Masih Aktif

| Resource        | Tipe                         | Estimasi Biaya                       |
| --------------- | ---------------------------- | ------------------------------------ |
| `urisai-maps`   | Azure Maps G2                | Per request, ~$0 untuk traffic kecil |
| `urisaistorage` | Storage Account Standard LRS | <$0.10/bulan                         |
| `urisai-kv`     | Key Vault                    | ~$0                                  |

### Resource yang Dihapus/Di-stop

| Resource                       | Status                     |
| ------------------------------ | -------------------------- |
| `urisai-mysql`                 | **Dihapus permanen**       |
| `urisai-plan` (App Service B1) | Sudah tidak ada sebelumnya |
| `urisai-api` (App Service)     | Sudah tidak ada sebelumnya |

### Stack Aktif

| Komponen    | Provider           | Biaya              |
| ----------- | ------------------ | ------------------ |
| Backend API | Google Cloud Run   | Gratis (free tier) |
| Database    | Neon PostgreSQL    | Gratis (free tier) |
| Peta        | Azure Maps         | Per request        |
| Storage     | Azure Blob Storage | <$0.10/bulan       |

**Estimasi total biaya bulanan: < $1/bulan**

### Endpoint Aktif

- **API:** `https://urisai-api-zgwts4p3va-as.a.run.app`
- **Health check:** `https://urisai-api-zgwts4p3va-as.a.run.app/health`
- **Dashboard data:** `https://urisai-api-zgwts4p3va-as.a.run.app/api/dashboard`
