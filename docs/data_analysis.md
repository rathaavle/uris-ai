# Analisis Data URIS-AI

**Urban Risk Intelligence System — Jakarta & Jawa Barat**
_From Data to Decision for Smarter Urban Resilience_

> **Catatan:** Data yang ditampilkan saat ini adalah **data simulasi** untuk keperluan demo.
> Pada implementasi produksi, seluruh data akan menggunakan sumber real-time dari BMKG,
> PetaBencana, dan OpenStreetMap secara otomatis.

---

## 1. Ringkasan Sumber Data

URIS-AI mengintegrasikan **5 sumber data** yang dikumpulkan dan disimpan di `data/raw/`.

| Sumber               | File                               | Jumlah Data                     | Lisensi                      |
| -------------------- | ---------------------------------- | ------------------------------- | ---------------------------- |
| BMKG API             | `bmkg/prakiraan_cuaca.csv`         | 432 baris, 24 wilayah           | Terbuka, atribusi BMKG       |
| PetaBencana.id       | `petabencana/flood_reports.csv`    | Real-time (simulasi untuk demo) | CC BY 4.0                    |
| OpenStreetMap        | `osm/roads.csv`                    | 27.835 ruas jalan               | ODbL 1.0                     |
| OpenStreetMap        | `osm/fasilitas_kesehatan.csv`      | 3.580 fasilitas                 | ODbL 1.0                     |
| OpenStreetMap        | `osm/fasilitas_publik.csv`         | 7.653 fasilitas                 | ODbL 1.0                     |
| Wilayah Administrasi | `wilayah/wilayah_administrasi.csv` | 25 kecamatan                    | Publik (Permendagri 72/2019) |

---

## 2. Detail Setiap Sumber Data

### 2.1 BMKG — Prakiraan Cuaca

**Endpoint:** `https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={kode_adm4}`

**Cara pengambilan:**

1. Script `scripts/collect_raw_data.py` memanggil API BMKG untuk setiap kode ADM4
2. Setiap wilayah menghasilkan prakiraan 3 hari ke depan dengan interval 3 jam
3. Data disimpan ke `data/raw/bmkg/prakiraan_cuaca.csv`
4. Pada produksi: Azure Function memanggil API ini setiap 6 jam secara otomatis

**Kolom penting:**

| Kolom                | Keterangan         | Satuan | Rentang Valid |
| -------------------- | ------------------ | ------ | ------------- |
| `suhu_c`             | Suhu udara         | °C     | -10 hingga 50 |
| `kelembaban_pct`     | Kelembaban relatif | %      | 0–100         |
| `curah_hujan_mm`     | Curah hujan        | mm     | ≥ 0           |
| `kecepatan_angin_ms` | Kecepatan angin    | m/s    | ≥ 0           |
| `tutupan_awan_pct`   | Persentase awan    | %      | 0–100         |
| `cuaca_kode`         | Kode kondisi cuaca | —      | 0–97          |

**Kode cuaca BMKG dan relevansinya terhadap banjir:**

| Kode | Kondisi           | Relevansi Banjir |
| ---- | ----------------- | ---------------- |
| 0–3  | Cerah / Berawan   | Tidak relevan    |
| 60   | Hujan Ringan      | Rendah           |
| 61   | Hujan Sedang      | Sedang           |
| 63   | Hujan Lebat       | Tinggi           |
| 80   | Hujan Lokal       | Sedang           |
| 95   | Hujan Petir       | Tinggi           |
| 97   | Hujan Petir Lebat | Sangat Tinggi    |

**Catatan:** Kode ADM4 Depok (`32.76.01.1001`) mengembalikan 404 dari BMKG.
Kode yang tepat perlu dicari di direktori ADM4 BMKG terbaru.

---

### 2.2 PetaBencana.id — Laporan Banjir

**Endpoint:** `https://data.petabencana.id/floods?city=jbd`

**Cara pengambilan:**

1. API dipanggil setiap 15 menit via Azure Function (pada produksi)
2. Mengembalikan laporan banjir aktif per kelurahan di Jakarta
3. Tingkat banjir (state) 1–4 digunakan sebagai input Traffic Analyzer

**Tingkat banjir:**

| State | Keterangan               | Dampak Jalan                            |
| ----- | ------------------------ | --------------------------------------- |
| 1     | Rendah (< 10 cm)         | Jalan masih bisa dilalui                |
| 2     | Sedang (10–70 cm)        | Kendaraan rendah terhambat              |
| 3     | Tinggi (70–150 cm)       | Sebagian besar jalan tidak bisa dilalui |
| 4     | Sangat Tinggi (> 150 cm) | Semua jalan tidak bisa dilalui          |

**Status demo:** Data banjir saat ini adalah simulasi berbasis data historis.
Pada produksi, data ini akan real-time dari sensor IoT dan laporan komunitas PetaBencana.

---

### 2.3 OpenStreetMap — Jaringan Jalan

**Endpoint:** `https://overpass-api.de/api/interpreter`

**Cara pengambilan:**

1. Script `scripts/collect_osm_roads.py` mengirim query Overpass API per kota
2. Filter tipe jalan: motorway, trunk, primary, secondary, tertiary
3. Data disimpan ke `data/raw/osm/roads.csv`
4. Update bulanan — OSM diperbarui oleh komunitas secara kontinu

**Statistik per kota:**

| Kota      | Ruas Jalan  | Tipe Dominan        |
| --------- | ----------- | ------------------- |
| Jakarta   | ~18.527     | primary, secondary  |
| Bandung   | ~4.772      | secondary, tertiary |
| Bogor     | ~1.223      | tertiary            |
| Bekasi    | ~2.248      | secondary           |
| Depok     | ~1.065      | tertiary            |
| **Total** | **~27.835** | —                   |

---

### 2.4 OpenStreetMap — Fasilitas Publik

**Fasilitas kesehatan (3.580 titik):**

| Tipe OSM      | Keterangan         |
| ------------- | ------------------ |
| `hospital`    | Rumah sakit        |
| `clinic`      | Klinik             |
| `doctors`     | Praktik dokter     |
| `pharmacy`    | Apotek             |
| `health_post` | Puskesmas pembantu |

**Fasilitas publik (7.653 titik):**

| Tipe OSM       | Keterangan           |
| -------------- | -------------------- |
| `school`       | Sekolah SD/SMP/SMA   |
| `university`   | Perguruan tinggi     |
| `government`   | Kantor pemerintah    |
| `townhall`     | Balai kota/kelurahan |
| `fire_station` | Pemadam kebakaran    |
| `police`       | Kantor polisi        |

---

### 2.5 Wilayah Administrasi

**25 Wilayah Target:**

| No  | Wilayah           | Kota            | Provinsi    | Elevasi (m) | Drainage |
| --- | ----------------- | --------------- | ----------- | ----------- | -------- |
| 1   | Menteng           | Jakarta Pusat   | DKI Jakarta | 7           | 150      |
| 2   | Tanah Abang       | Jakarta Pusat   | DKI Jakarta | 5           | 120      |
| 3   | Kemayoran         | Jakarta Pusat   | DKI Jakarta | 8           | 180      |
| 4   | Kelapa Gading     | Jakarta Utara   | DKI Jakarta | 3           | 100      |
| 5   | Penjaringan       | Jakarta Utara   | DKI Jakarta | 2           | 80       |
| 6   | Pademangan        | Jakarta Utara   | DKI Jakarta | 4           | 110      |
| 7   | Kebayoran Baru    | Jakarta Selatan | DKI Jakarta | 15          | 200      |
| 8   | Tebet             | Jakarta Selatan | DKI Jakarta | 12          | 170      |
| 9   | Cilandak          | Jakarta Selatan | DKI Jakarta | 50          | 250      |
| 10  | Cengkareng        | Jakarta Barat   | DKI Jakarta | 6           | 130      |
| 11  | Kebon Jeruk       | Jakarta Barat   | DKI Jakarta | 10          | 160      |
| 12  | Grogol Petamburan | Jakarta Barat   | DKI Jakarta | 8           | 140      |
| 13  | Matraman          | Jakarta Timur   | DKI Jakarta | 9           | 145      |
| 14  | Jatinegara        | Jakarta Timur   | DKI Jakarta | 7           | 135      |
| 15  | Cakung            | Jakarta Timur   | DKI Jakarta | 5           | 115      |
| 16  | Bandung Wetan     | Kota Bandung    | Jawa Barat  | 768         | 220      |
| 17  | Cicendo           | Kota Bandung    | Jawa Barat  | 750         | 210      |
| 18  | Coblong           | Kota Bandung    | Jawa Barat  | 800         | 240      |
| 19  | Bogor Tengah      | Kota Bogor      | Jawa Barat  | 290         | 190      |
| 20  | Bogor Utara       | Kota Bogor      | Jawa Barat  | 250         | 180      |
| 21  | Tanah Sareal      | Kota Bogor      | Jawa Barat  | 270         | 185      |
| 22  | Bekasi Timur      | Kota Bekasi     | Jawa Barat  | 19          | 125      |
| 23  | Bekasi Barat      | Kota Bekasi     | Jawa Barat  | 15          | 120      |
| 24  | Pondok Gede       | Kota Bekasi     | Jawa Barat  | 22          | 130      |
| 25  | Depok             | Kota Depok      | Jawa Barat  | 80          | 165      |

---

## 3. Proses Pengolahan Data

### 3.1 Pipeline Data

```
Sumber Eksternal          Pengumpulan              Penyimpanan
─────────────────         ───────────              ───────────
BMKG API          ──→  collect_raw_data.py   ──→  data/raw/bmkg/
PetaBencana API   ──→  Azure Function (15m)  ──→  data/raw/petabencana/
OSM Overpass      ──→  collect_osm_roads.py  ──→  data/raw/osm/
                                                       │
                                                       ▼
                                               Azure Blob Storage
                                               (urisaistorage)
                                                       │
                                                       ▼
                                               Data Processing
                                               (DataCleaner,
                                                FeatureEngineer)
                                                       │
                                                       ▼
                                               Azure MySQL
                                               (uris-ai-db)
                                                       │
                                                       ▼
                                               ML Engine
                                               (FloodRiskEngine,
                                                RiskScoringEngine)
                                                       │
                                                       ▼
                                               FastAPI → Dashboard
```

### 3.2 Validasi Data

| Kolom            | Aturan Validasi                      |
| ---------------- | ------------------------------------ |
| `suhu_c`         | -10 ≤ nilai ≤ 50                     |
| `kelembaban_pct` | 0 ≤ nilai ≤ 100                      |
| `curah_hujan_mm` | nilai ≥ 0                            |
| `state` (banjir) | 1 ≤ nilai ≤ 4                        |
| `lat`/`lon`      | Dalam batas geografis wilayah target |

---

## 4. Urban Risk Score (URS) — Penjelasan Angka

### 4.1 Formula

```
URS = (flood_risk × 0.5) + (traffic_impact × 0.3) + (service_access × 0.2)
```

**Bobot dipilih berdasarkan:**

- Banjir (50%) — faktor utama risiko urban di Jakarta
- Lalu lintas (30%) — dampak langsung ke mobilitas dan evakuasi
- Aksesibilitas layanan (20%) — dampak ke fasilitas kritis

### 4.2 Kategori URS

| Kategori | Rentang | Warna     | Interpretasi                 |
| -------- | ------- | --------- | ---------------------------- |
| RENDAH   | 0–25    | 🟢 Hijau  | Kondisi normal               |
| SEDANG   | 26–50   | 🟡 Kuning | Waspada, pantau perkembangan |
| TINGGI   | 51–75   | 🔴 Merah  | Siaga, persiapkan respons    |
| KRITIS   | 76–100  | 🟣 Ungu   | Darurat, tindakan segera     |

### 4.3 Analisis Angka URS Demo

**Status saat ini:** URS dihitung menggunakan **simulasi berbasis data geografis**
(elevasi + drainage capacity) untuk keperluan demo. Ini by design — angka yang
dihasilkan tetap masuk akal secara geografis dan representatif untuk menunjukkan
kemampuan sistem.

**Pada produksi:** URS akan dihitung dari model ML (scikit-learn RandomForest)
yang dilatih dengan data cuaca BMKG real-time + historis banjir aktual.

**Mengapa angkanya masuk akal secara geografis:**

| Wilayah               | URS    | Alasan Geografis                                       |
| --------------------- | ------ | ------------------------------------------------------ |
| Penjaringan (54.67)   | TINGGI | Elevasi 2m, pesisir utara Jakarta, drainage buruk (80) |
| Pademangan (50.69)    | TINGGI | Elevasi 4m, dekat pantai, drainage 110                 |
| Kelapa Gading (46.69) | SEDANG | Elevasi 3m, tapi drainage lebih baik                   |
| Tanah Abang (44.24)   | SEDANG | Elevasi 5m, pusat kota, drainage sedang                |
| Bandung Wetan (5.0)   | RENDAH | Elevasi 768m, dataran tinggi, drainage sangat baik     |
| Cilandak (8.01)       | RENDAH | Elevasi 50m, Jakarta Selatan, drainage baik            |
| Kebayoran Baru (8.05) | RENDAH | Elevasi 15m, drainage baik (200)                       |

**Kesimpulan:** Angka simulasi ini mencerminkan kondisi geografis nyata wilayah-wilayah
tersebut. Jakarta Utara (elevasi rendah, dekat pantai) memang lebih rawan banjir
dibanding Jakarta Selatan atau kota-kota Jawa Barat yang berada di dataran tinggi.

---

## 5. Kesesuaian dengan Requirements

### Yang Sudah Sesuai ✅

| Requirement                        | Status | Teknologi                                     |
| ---------------------------------- | ------ | --------------------------------------------- |
| Req 2: Urban Risk Score 0–100      | ✅     | RiskScoringEngine                             |
| Req 3: Analisis dampak kemacetan   | ✅     | TrafficAnalyzer + OSM 27.835 jalan            |
| Req 4: Aksesibilitas fasilitas     | ✅     | ServiceAccessibilityModule + 11.233 fasilitas |
| Req 5: Rekomendasi rute            | ✅     | RecommendationEngine                          |
| Req 6: Integrasi data multi-sumber | ✅     | BMKG + PetaBencana + OSM                      |
| Req 7: Dashboard interaktif        | ✅     | HTML/CSS/JS + Azure Maps + flood overlay      |
| Req 8: Auth 2 peran                | ✅     | JWT sha256_crypt                              |
| Req 10: Keamanan                   | ✅     | Key Vault + TLS + MySQL SSL                   |
| Req 11: Transparansi AI            | ✅     | Disclaimer popup "Data Simulasi"              |
| Req 12: Azure infrastructure       | ✅     | MySQL free tier B1MS                          |

### Direncanakan untuk Produksi 🔲

| Requirement                   | Gap                                           | Rencana                   |
| ----------------------------- | --------------------------------------------- | ------------------------- |
| Req 1: Prediksi ML real       | Data simulasi → produksi pakai BMKG real-time | Task 22–23                |
| Req 1.2: F1-score ≥ 0.75      | Perlu training dengan data historis aktual    | Task 23                   |
| Req 9.4: Redis cache          | Belum aktif                                   | Task 19.2 (Upstash Redis) |
| Req 13: Notifikasi darurat    | Belum diimplementasi                          | Task 24                   |
| Req 14: Laporan kualitas data | Belum ada endpoint                            | Task 26                   |
| Req 15: Auto-retrain 30 hari  | Belum ada scheduler                           | Task 25                   |

---

## 6. Potensi Dampak ke Ketahanan Kota

### 6.1 Dampak Langsung (Saat Produksi)

**Respons Darurat Lebih Cepat**

- Tanpa URIS-AI: BPBD menunggu laporan manual → respons 2–4 jam
- Dengan URIS-AI: Notifikasi otomatis saat URS ≥ 76 → respons < 2 menit
- **Estimasi pengurangan waktu respons: 60–90%**

**Pengurangan Kemacetan saat Banjir**

- 27.835 ruas jalan dipantau → rute alternatif real-time
- Pengguna menghindari jalan tergenang sebelum terjebak
- **Estimasi pengurangan waktu perjalanan: 20–40% saat banjir**

**Aksesibilitas Fasilitas Kritis**

- 3.580 fasilitas kesehatan dipantau aksesibilitasnya
- Pasien diarahkan ke RS alternatif sebelum RS utama terisolasi
- **Estimasi pengurangan keterlambatan penanganan medis: 30–50%**

### 6.2 Dampak Jangka Menengah

**Prioritisasi Anggaran Infrastruktur**

- Data URS historis menunjukkan wilayah paling sering berisiko tinggi
- Pemerintah memprioritaskan perbaikan drainase di wilayah TINGGI/KRITIS
- Contoh: Penjaringan dan Pademangan perlu investasi drainase prioritas

**Perencanaan Tata Kota**

- Elevasi + drainage + flood history = input untuk RTRW
- Wilayah URS konsisten TINGGI dapat dipertimbangkan untuk pembatasan pembangunan

### 6.3 Dampak Jangka Panjang

**Model ML yang Semakin Akurat**

- Setiap kejadian banjir memperkaya training data
- Setelah 1–2 tahun operasional, model dapat mencapai F1-score > 0.85
- Prediksi banjir 6–12 jam ke depan menjadi lebih andal

**Integrasi dengan Ekosistem Kota**

- ATCS Jakarta (traffic management)
- Aplikasi warga: JAKI, PetaBencana
- Sistem peringatan dini BPBD

---

## 7. User System — Analisis Kecukupan

### Kondisi Saat Ini (Demo)

| User     | Role       | Akses                      |
| -------- | ---------- | -------------------------- |
| `admin`  | government | Penuh — semua endpoint     |
| `public` | public     | Terbatas — peta, URS, rute |

**Untuk demo: Sudah cukup.**

### Kebutuhan Produksi

| Kebutuhan                 | Alasan                                         | Prioritas |
| ------------------------- | ---------------------------------------------- | --------- |
| Registrasi user mandiri   | Saat ini hanya via script                      | Sedang    |
| Multiple government users | BPBD, Dinas Perhubungan, Dinas Kesehatan       | Tinggi    |
| Token refresh endpoint    | Token 30 menit terlalu pendek untuk monitoring | Sedang    |
| Password reset            | Tidak ada mekanisme reset saat ini             | Sedang    |
| Audit log per user        | Siapa mengakses apa dan kapan                  | Rendah    |

---

## 8. Validasi Teknologi

### Database: Azure Database for MySQL (Free Tier B1MS)

| Aspek           | MySQL                                  | Alternatif                                |
| --------------- | -------------------------------------- | ----------------------------------------- |
| Biaya           | **Gratis** (free tier 750 jam/bulan)   | PostgreSQL (tidak ada di free tier Azure) |
| Performa        | Cukup untuk 25 wilayah + 1000 req/hari | —                                         |
| Kompatibilitas  | SQLAlchemy + PyMySQL ✅                | —                                         |
| **Rekomendasi** | **Tetap MySQL** untuk sekarang         | Upgrade jika traffic meningkat            |

### Maps: Azure Maps Gen2

| Aspek           | Azure Maps                                     | Alternatif                                        |
| --------------- | ---------------------------------------------- | ------------------------------------------------- |
| Biaya           | 250.000 tile/bulan gratis                      | Google Maps ($7/1000 req), Mapbox ($0.5/1000 req) |
| Kualitas        | Sangat baik, data TomTom                       | Google Maps lebih familiar                        |
| **Rekomendasi** | **Tetap Azure Maps** — gratis dan native Azure |

### ML: scikit-learn (in-process)

| Aspek           | scikit-learn                     | Alternatif                         |
| --------------- | -------------------------------- | ---------------------------------- |
| Biaya           | **Gratis**                       | Azure ML ($0.10/jam compute)       |
| Deployment      | In-process FastAPI               | Azure ML endpoint (lebih scalable) |
| **Rekomendasi** | **Tetap scikit-learn** untuk MVP |

### Cache: Redis (Belum Aktif)

| Aspek           | Azure Cache for Redis                     | Upstash Redis                             |
| --------------- | ----------------------------------------- | ----------------------------------------- |
| Biaya           | Tidak ada di free tier                    | **Gratis** (10.000 req/hari)              |
| Setup           | Perlu provisioning Azure                  | Daftar di upstash.com, dapat URL langsung |
| **Rekomendasi** | **Gunakan Upstash Redis** untuk free tier |

---

## 9. Roadmap Data Improvement

| Prioritas | Task                                                | Dampak                    |
| --------- | --------------------------------------------------- | ------------------------- |
| 🔴 Tinggi | Import data BMKG ke MySQL (Task 22)                 | Model ML bisa dilatih     |
| 🔴 Tinggi | Training FloodRiskEngine dengan data real (Task 23) | URS berbasis prediksi ML  |
| 🟡 Sedang | Aktifkan Upstash Redis cache                        | Response time < 500ms     |
| 🟡 Sedang | Integrasi data historis banjir BNPB/inaRISK         | Training data lebih kaya  |
| 🟢 Rendah | Auto-retrain model setiap 30 hari (Task 25)         | Model terus meningkat     |
| 🟢 Rendah | Tambah data curah hujan historis BMKG               | Validasi model lebih baik |

---

_Dokumen ini diperbarui: 2026-06-01_
_Dikompilasi dari: `data/raw/catatan_data_raw.md`, source code URIS-AI, dan analisis geografis_
