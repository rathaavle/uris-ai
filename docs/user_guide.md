# Panduan Pengguna URIS-AI

**Urban Risk Intelligence System for Flood-Aware Mobility and Public Service Optimization**

**Versi:** 1.0.0  
**Terakhir Diperbarui:** 20 Januari 2024

---

## Daftar Isi

1. [Pengenalan](#pengenalan)
2. [Memulai](#memulai)
3. [Panduan Dashboard](#panduan-dashboard)
4. [Fitur Utama](#fitur-utama)
5. [FAQ](#faq)
6. [Troubleshooting](#troubleshooting)
7. [Kontak & Dukungan](#kontak--dukungan)

---

## Pengenalan

### Apa itu URIS-AI?

URIS-AI adalah sistem kecerdasan buatan yang membantu Anda memahami dan mengantisipasi risiko banjir di wilayah Jakarta dan Jawa Barat. Sistem ini mengintegrasikan data cuaca, historis banjir, kondisi lalu lintas, dan aksesibilitas fasilitas publik untuk memberikan informasi yang akurat dan rekomendasi tindakan yang tepat.

### Siapa yang Dapat Menggunakan URIS-AI?

URIS-AI dirancang untuk tiga kelompok pengguna:

1. **Masyarakat Umum** - Melihat kondisi risiko banjir, mencari rute aman, dan mendapatkan informasi fasilitas publik alternatif
2. **Pengelola Fasilitas Publik** - Memantau aksesibilitas fasilitas (rumah sakit, puskesmas, sekolah) dan mengkoordinasikan pengalihan layanan
3. **Petugas Pemerintah** - Memantau risiko secara komprehensif, mengatur respons darurat, dan mengalokasikan sumber daya

### Manfaat Utama

✅ **Prediksi Dini** - Dapatkan peringatan risiko banjir sebelum terjadi  
✅ **Rute Aman** - Temukan jalur alternatif yang menghindari wilayah berisiko tinggi  
✅ **Informasi Real-Time** - Data diperbarui setiap 5-10 menit  
✅ **Rekomendasi Cerdas** - Saran tindakan spesifik berdasarkan kondisi aktual  
✅ **Visualisasi Mudah** - Peta interaktif dengan kode warna yang jelas

**Requirements:** 6.3

---

## Memulai

### Akses Dashboard

1. Buka browser web (Chrome, Firefox, Safari, atau Edge)
2. Kunjungi: **https://dashboard.uris-ai.go.id**
3. Anda akan melihat halaman login

### Login ke Sistem

**Untuk Masyarakat Umum:**

- Klik tombol **"Akses Publik"** untuk masuk tanpa login
- Anda dapat melihat peta risiko dan mencari rute aman

**Untuk Pengelola Fasilitas & Petugas Pemerintah:**

1. Masukkan **Username** (email Anda)
2. Masukkan **Password**
3. Klik tombol **"Login"**

> **Catatan:** Jika Anda lupa password, hubungi administrator sistem di admin@uris-ai.go.id

### Tampilan Pertama

Setelah login, Anda akan melihat:

- **Peta Interaktif** di tengah layar dengan warna-warna yang menunjukkan tingkat risiko
- **Panel Informasi** di sisi kiri dengan filter dan parameter
- **Panel Detail** di sisi kanan yang muncul saat Anda memilih wilayah

---

## Panduan Dashboard

### Memahami Peta Risiko

Dashboard menampilkan peta Jakarta dan Jawa Barat dengan kode warna:

| Warna     | Kategori   | Urban Risk Score | Arti                              |
| --------- | ---------- | ---------------- | --------------------------------- |
| 🟢 Hijau  | **RENDAH** | 0-30             | Aman, tidak ada risiko signifikan |
| 🟡 Kuning | **SEDANG** | 31-60            | Waspada, pantau perkembangan      |
| 🟠 Oranye | **TINGGI** | 61-85            | Hindari jika memungkinkan         |
| 🔴 Merah  | **KRITIS** | 86-100           | Bahaya! Jangan memasuki wilayah   |

### Navigasi Peta

**Zoom In/Out:**

- Gunakan tombol **+** dan **-** di pojok kiri atas
- Atau gunakan scroll mouse/trackpad

**Geser Peta:**

- Klik dan tahan, lalu geser mouse
- Atau gunakan gesture swipe di touchscreen

**Pilih Wilayah:**

- Klik pada wilayah di peta
- Panel detail akan muncul di sisi kanan

### Panel Filter

Di sisi kiri, Anda dapat menyesuaikan tampilan:

**Filter Waktu:**

- **Real-Time** - Data terkini (default)
- **1 Jam Ke Depan** - Prediksi 1 jam
- **3 Jam Ke Depan** - Prediksi 3 jam
- **6 Jam Ke Depan** - Prediksi 6 jam

**Filter Kategori Risiko:**

- Centang/hapus centang kategori untuk menampilkan/menyembunyikan wilayah dengan kategori tertentu
- Contoh: Hanya tampilkan wilayah dengan risiko TINGGI dan KRITIS

**Filter Wilayah:**

- Pilih provinsi: Jakarta atau Jawa Barat
- Pilih kota/kabupaten untuk fokus pada area tertentu

### Panel Detail Wilayah

Saat Anda memilih wilayah, panel detail menampilkan:

**Informasi Risiko:**

- **Urban Risk Score** - Skor terpadu (0-100)
- **Kategori Risiko** - RENDAH/SEDANG/TINGGI/KRITIS
- **Risiko Banjir** - Skor prediksi banjir (0-100)
- **Dampak Lalu Lintas** - Skor kemacetan (0-100)
- **Aksesibilitas Layanan** - Skor gangguan fasilitas publik (0-100)

**Grafik Tren:**

- Menampilkan perubahan Urban Risk Score dalam 24 jam terakhir
- Garis naik = risiko meningkat
- Garis turun = risiko menurun

**Rekomendasi Tindakan:**

- Daftar saran spesifik berdasarkan kondisi saat ini
- Setiap rekomendasi memiliki label urgensi:
  - 🔴 **Segera** - Tindakan dalam 1 jam
  - 🟠 **Waspada** - Tindakan dalam 1-6 jam
  - 🟡 **Siaga** - Tindakan dalam 6-24 jam

**Fasilitas Publik Terdampak:**

- Daftar rumah sakit, puskesmas, sekolah yang aksesnya terganggu
- Fasilitas alternatif yang masih dapat diakses

---

## Fitur Utama

### 1. Melihat Risiko Wilayah

**Langkah-langkah:**

1. Buka dashboard
2. Lihat peta dengan kode warna
3. Klik wilayah yang ingin Anda ketahui
4. Baca informasi detail di panel kanan

**Tips:**

- Wilayah dengan warna merah/oranye sebaiknya dihindari
- Perhatikan grafik tren untuk melihat apakah risiko naik atau turun
- Baca rekomendasi tindakan untuk panduan spesifik

### 2. Mencari Rute Aman

**Langkah-langkah:**

1. Klik tombol **"Cari Rute Aman"** di bagian atas
2. Masukkan **Titik Asal** (atau klik "Gunakan Lokasi Saya")
3. Masukkan **Titik Tujuan**
4. Klik **"Cari Rute"**
5. Sistem akan menampilkan:
   - Rute yang menghindari wilayah berisiko tinggi
   - Wilayah yang dihindari (ditandai dengan warna merah)
   - Estimasi waktu perjalanan

**Jika Tidak Ada Rute Aman:**

- Sistem akan menampilkan pesan: "Semua rute menuju tujuan melewati wilayah dengan risiko Tinggi atau Kritis"
- Anda akan melihat estimasi waktu pemulihan (berapa jam lagi rute akan aman)
- Pertimbangkan untuk menunda perjalanan atau gunakan transportasi alternatif

**Tips:**

- Selalu cek rute sebelum berangkat saat musim hujan
- Simpan screenshot rute untuk referensi offline
- Perbarui pencarian rute jika kondisi berubah

### 3. Memantau Fasilitas Publik

**Untuk Masyarakat Umum:**

1. Klik ikon fasilitas di peta (rumah sakit, puskesmas, sekolah)
2. Lihat status aksesibilitas:
   - ✅ **Dapat Diakses** - Fasilitas beroperasi normal
   - ⚠️ **Akses Terganggu** - Jalan menuju fasilitas terdampak
   - ❌ **Tidak Dapat Diakses** - Fasilitas terisolasi
3. Jika terganggu, sistem akan menampilkan fasilitas alternatif terdekat

**Untuk Pengelola Fasilitas:**

1. Login dengan akun pengelola fasilitas
2. Klik menu **"Fasilitas Saya"**
3. Lihat status semua fasilitas yang Anda kelola
4. Terima notifikasi jika aksesibilitas berubah
5. Koordinasikan pengalihan layanan jika diperlukan

**Tips:**

- Fasilitas dengan label "Berpotensi Overload" mungkin penuh karena pengalihan pasien/pengguna
- Hubungi fasilitas alternatif sebelum pergi untuk memastikan ketersediaan

### 4. Menerima Notifikasi & Peringatan

**Mengaktifkan Notifikasi:**

1. Klik ikon **"Pengaturan"** (⚙️) di pojok kanan atas
2. Pilih **"Notifikasi"**
3. Aktifkan notifikasi untuk:
   - Peningkatan risiko di wilayah favorit
   - Rekomendasi tindakan mendesak
   - Perubahan status fasilitas publik

**Jenis Notifikasi:**

- 🔴 **Peringatan Kritis** - Risiko mencapai level KRITIS
- 🟠 **Peringatan Tinggi** - Risiko mencapai level TINGGI
- 🟡 **Informasi** - Perubahan kondisi umum

**Tips:**

- Tambahkan wilayah rumah dan kantor Anda ke favorit
- Aktifkan notifikasi push di browser untuk peringatan real-time
- Jangan abaikan notifikasi dengan label "Segera"

### 5. Melihat Tren Historis

**Langkah-langkah:**

1. Pilih wilayah di peta
2. Scroll ke bagian **"Grafik Tren"** di panel detail
3. Pilih rentang waktu:
   - 24 jam terakhir (default)
   - 48 jam terakhir
   - 7 hari terakhir
4. Analisis pola:
   - Apakah risiko cenderung naik atau turun?
   - Apakah ada pola berulang (misalnya, risiko tinggi setiap sore)?

**Tips:**

- Tren naik tajam = kondisi memburuk cepat, segera ambil tindakan
- Tren stabil tinggi = kondisi buruk berkepanjangan, hindari wilayah
- Tren turun = kondisi membaik, tapi tetap waspada

---

## FAQ

### Pertanyaan Umum

**Q: Seberapa sering data diperbarui?**  
A: Data cuaca dan risiko banjir diperbarui setiap 10 menit. Saat kondisi risiko aktif (kategori TINGGI atau KRITIS), pembaruan dilakukan setiap 5 menit.

**Q: Apakah saya perlu membayar untuk menggunakan URIS-AI?**  
A: Tidak. URIS-AI adalah layanan publik gratis yang disediakan oleh pemerintah.

**Q: Apakah URIS-AI bisa diakses dari smartphone?**  
A: Ya. Dashboard URIS-AI responsif dan dapat diakses dari smartphone, tablet, atau komputer melalui browser web.

**Q: Bagaimana cara mendapatkan akun untuk pengelola fasilitas atau petugas pemerintah?**  
A: Hubungi administrator sistem di admin@uris-ai.go.id dengan menyertakan:

- Nama lengkap
- Instansi/organisasi
- Email resmi
- Nomor telepon
- Peran yang diminta (pengelola fasilitas atau petugas pemerintah)

**Q: Apakah prediksi URIS-AI 100% akurat?**  
A: URIS-AI menggunakan model AI dengan akurasi minimal 80% berdasarkan validasi historis. Namun, kondisi cuaca dapat berubah cepat. Selalu gunakan penilaian Anda sendiri dan ikuti instruksi dari petugas berwenang.

**Q: Apa yang harus saya lakukan jika melihat wilayah saya berwarna merah (KRITIS)?**  
A:

1. Jangan memasuki atau tinggalkan wilayah jika memungkinkan
2. Baca rekomendasi tindakan di panel detail
3. Ikuti instruksi dari BPBD atau petugas setempat
4. Siapkan tas darurat dan dokumen penting
5. Pantau perkembangan melalui dashboard

**Q: Bagaimana cara melaporkan data yang tidak akurat?**  
A: Klik tombol **"Laporkan Masalah"** di panel detail wilayah, atau kirim email ke feedback@uris-ai.go.id dengan menyertakan:

- Lokasi/wilayah
- Waktu kejadian
- Deskripsi masalah
- Foto (jika ada)

### Pertanyaan Teknis

**Q: Browser apa yang didukung?**  
A: URIS-AI mendukung:

- Google Chrome 90+
- Mozilla Firefox 88+
- Safari 14+
- Microsoft Edge 90+

**Q: Apakah saya perlu menginstal aplikasi?**  
A: Tidak. URIS-AI adalah aplikasi web yang berjalan di browser. Tidak perlu instalasi.

**Q: Mengapa peta tidak muncul?**  
A: Pastikan:

- Koneksi internet Anda stabil
- JavaScript diaktifkan di browser
- Browser Anda up-to-date
- Tidak ada ad-blocker yang memblokir konten

**Q: Apakah data saya aman?**  
A: Ya. URIS-AI menggunakan enkripsi TLS 1.2+ untuk semua komunikasi. Data pribadi Anda tidak dibagikan kepada pihak ketiga.

**Q: Berapa banyak data internet yang digunakan?**  
A: Penggunaan data rata-rata:

- Membuka dashboard: ~2-3 MB
- Penggunaan normal (1 jam): ~5-10 MB
- Dengan notifikasi aktif: ~15-20 MB per hari

**Q: Apakah bisa digunakan offline?**  
A: Tidak. URIS-AI memerlukan koneksi internet untuk mengakses data real-time. Namun, Anda dapat mengambil screenshot untuk referensi offline.

---

## Troubleshooting

### Masalah Login

**Masalah:** "Username atau password salah"  
**Solusi:**

- Pastikan Caps Lock tidak aktif
- Periksa ejaan username dan password
- Gunakan fitur "Lupa Password" jika perlu
- Hubungi admin jika masalah berlanjut

**Masalah:** "Akun pengguna tidak aktif"  
**Solusi:**

- Akun Anda mungkin dinonaktifkan oleh administrator
- Hubungi admin@uris-ai.go.id untuk aktivasi ulang

### Masalah Tampilan

**Masalah:** Peta tidak muncul atau kosong  
**Solusi:**

1. Refresh halaman (tekan F5 atau Ctrl+R)
2. Clear cache browser
3. Coba browser lain
4. Periksa koneksi internet

**Masalah:** Warna peta tidak berubah saat filter diubah  
**Solusi:**

1. Tunggu beberapa detik (data sedang dimuat)
2. Refresh halaman
3. Periksa apakah ada pesan error di bagian bawah layar

**Masalah:** Panel detail tidak muncul saat wilayah diklik  
**Solusi:**

1. Pastikan Anda mengklik tepat di area wilayah (bukan di luar)
2. Zoom in untuk area yang lebih kecil
3. Refresh halaman

### Masalah Performa

**Masalah:** Dashboard lambat atau lag  
**Solusi:**

1. Tutup tab browser lain yang tidak digunakan
2. Nonaktifkan ekstensi browser yang tidak perlu
3. Gunakan mode "Performa Tinggi" di pengaturan dashboard
4. Kurangi rentang waktu tren (misalnya, dari 7 hari ke 24 jam)

**Masalah:** Notifikasi tidak muncul  
**Solusi:**

1. Periksa pengaturan notifikasi di dashboard
2. Izinkan notifikasi di pengaturan browser
3. Periksa apakah browser mendukung notifikasi push
4. Refresh halaman dan login ulang

### Masalah Data

**Masalah:** "Belum ada data risiko untuk wilayah ini"  
**Solusi:**

- Wilayah tersebut mungkin baru ditambahkan dan belum ada data historis
- Coba lagi dalam beberapa jam
- Hubungi support jika masalah berlanjut

**Masalah:** Data terlihat tidak akurat  
**Solusi:**

1. Periksa timestamp "Terakhir Diperbarui" di panel detail
2. Refresh halaman untuk data terbaru
3. Laporkan masalah melalui tombol "Laporkan Masalah"

---

## Kontak & Dukungan

### Tim Dukungan

**Email Umum:** support@uris-ai.go.id  
**Email Teknis:** tech-support@uris-ai.go.id  
**Email Administrator:** admin@uris-ai.go.id  
**Email Feedback:** feedback@uris-ai.go.id

**Jam Operasional:**

- Senin - Jumat: 08:00 - 17:00 WIB
- Sabtu: 08:00 - 12:00 WIB
- Minggu & Libur: Tutup (kecuali kondisi darurat)

### Darurat

Untuk kondisi darurat banjir, hubungi:

- **BPBD DKI Jakarta:** 021-1234567
- **BPBD Jawa Barat:** 022-7654321
- **Call Center 112:** Layanan darurat nasional

### Media Sosial

- Twitter: @URISAI_Official
- Instagram: @urisai.official
- Facebook: URIS-AI Indonesia

### Dokumentasi Tambahan

- **Website:** https://uris-ai.go.id
- **Dokumentasi API:** https://docs.uris-ai.go.id/api
- **Video Tutorial:** https://youtube.com/@urisai
- **Status Sistem:** https://status.uris-ai.go.id

---

## Lampiran: Istilah Penting

**Urban Risk Score (URS)** - Skor terpadu (0-100) yang menggabungkan risiko banjir, dampak lalu lintas, dan gangguan layanan publik.

**Kategori Risiko** - Klasifikasi risiko: RENDAH (0-30), SEDANG (31-60), TINGGI (61-85), KRITIS (86-100).

**Wilayah** - Unit geografis administratif (kelurahan/kecamatan) yang menjadi unit analisis.

**Fasilitas Publik** - Rumah sakit, puskesmas, kantor pemerintahan, dan sekolah yang dipantau aksesibilitasnya.

**Rute Aman** - Jalur perjalanan yang menghindari wilayah dengan kategori risiko TINGGI atau KRITIS.

**Urgensi** - Tingkat kemendesakan rekomendasi: Segera (1 jam), Waspada (1-6 jam), Siaga (6-24 jam).

---

**Terima kasih telah menggunakan URIS-AI!**

Sistem ini dikembangkan untuk membantu masyarakat mengantisipasi dan merespons risiko banjir dengan lebih baik. Feedback dan saran Anda sangat berharga untuk perbaikan sistem.

**Tetap Aman, Tetap Waspada!** 🌊🚨
