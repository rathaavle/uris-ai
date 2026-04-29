# Dokumen Persyaratan

## Pendahuluan

URIS-AI (Urban Risk Intelligence System for Flood-Aware Mobility and Public Service Optimization) adalah sistem berbasis kecerdasan buatan yang mengintegrasikan data cuaca, historis banjir, jaringan transportasi, dan fasilitas publik untuk memprediksi risiko urban secara komprehensif di wilayah Jakarta dan Jawa Barat.

Sistem ini dirancang untuk mengubah pendekatan penanganan banjir dari reaktif menjadi proaktif, dengan menyediakan prediksi risiko, analisis dampak lalu lintas, pemantauan aksesibilitas layanan publik, serta rekomendasi tindakan berbasis data bagi pemerintah daerah, pengelola fasilitas publik, dan masyarakat umum.

**Tagline**: _From Data to Decision for Smarter Urban Resilience_

---

## Glosarium

- **URIS-AI**: Urban Risk Intelligence System — sistem utama yang menjadi subjek dokumen ini.
- **Flood_Risk_Engine**: Komponen AI yang memproses data cuaca dan historis banjir untuk menghasilkan prediksi risiko banjir.
- **Traffic_Analyzer**: Komponen yang menganalisis dampak banjir terhadap kondisi lalu lintas.
- **Service_Accessibility_Module**: Komponen yang memantau dan mengevaluasi aksesibilitas fasilitas publik saat terjadi gangguan.
- **Risk_Scoring_Engine**: Komponen yang mengintegrasikan output dari berbagai modul untuk menghasilkan Urban Risk Score.
- **Recommendation_Engine**: Komponen yang menghasilkan rekomendasi tindakan berbasis skor risiko dan kondisi aktual.
- **Dashboard**: Antarmuka pengguna berbasis web yang menampilkan visualisasi peta interaktif dan informasi risiko.
- **Data_Integrator**: Komponen yang mengambil, menggabungkan, dan menyinkronkan data dari berbagai sumber eksternal.
- **Urban Risk Score (URS)**: Skor terpadu (0–100) yang merepresentasikan tingkat risiko urban suatu wilayah pada waktu tertentu, dihitung dari kombinasi risiko banjir, dampak lalu lintas, dan gangguan layanan publik.
- **Wilayah**: Unit geografis administratif (kelurahan/kecamatan) di Jakarta dan Jawa Barat yang menjadi unit analisis URIS-AI.
- **Fasilitas Publik**: Infrastruktur layanan masyarakat yang dipantau, mencakup rumah sakit, puskesmas, kantor pemerintahan, dan sekolah.
- **Pengguna**: Aktor yang mengakses URIS-AI, terdiri dari tiga peran: Pemerintah (BPBD, Dinas Perhubungan), Pengelola Fasilitas, dan Masyarakat Umum.
- **Azure**: Platform cloud Microsoft yang digunakan untuk deployment, pemrosesan data, dan hosting model AI URIS-AI.
- **Near Real-Time**: Pemrosesan dan penyajian data dengan latensi tidak lebih dari 60 detik dari waktu data tersedia.

---

## Persyaratan

### Persyaratan 1: Prediksi Risiko Banjir

**User Story:** Sebagai petugas BPBD, saya ingin mendapatkan prediksi risiko banjir per wilayah secara otomatis, sehingga saya dapat mempersiapkan respons darurat sebelum banjir terjadi.

#### Kriteria Penerimaan

1. WHEN data cuaca terbaru diterima oleh Data_Integrator, THE Flood_Risk_Engine SHALL memperbarui prediksi risiko banjir untuk setiap Wilayah dalam waktu tidak lebih dari 60 detik.
2. WHEN data historis banjir diperbarui, THE Flood_Risk_Engine SHALL menggabungkan data historis tersebut dengan data cuaca terkini untuk menghasilkan prediksi risiko banjir.
3. WHEN Pengguna memilih suatu Wilayah pada Dashboard, THE Flood_Risk_Engine SHALL menampilkan tingkat risiko banjir Wilayah tersebut dalam kategori: Rendah, Sedang, Tinggi, atau Kritis, beserta nilai skor numerik (0–100).
4. IF data cuaca dari sumber eksternal tidak tersedia lebih dari 10 menit, THEN THE Flood_Risk_Engine SHALL menggunakan data cuaca terakhir yang valid dan menampilkan indikator peringatan keterlambatan data kepada Pengguna.
5. THE Flood_Risk_Engine SHALL menghasilkan prediksi risiko banjir dengan akurasi minimal 80% berdasarkan validasi terhadap data historis banjir yang telah terjadi.

---

### Persyaratan 2: Analisis Dampak Lalu Lintas

**User Story:** Sebagai petugas Dinas Perhubungan, saya ingin mengetahui dampak banjir terhadap kondisi lalu lintas, sehingga saya dapat mengatur rekayasa lalu lintas secara proaktif.

#### Kriteria Penerimaan

1. WHEN Flood_Risk_Engine mendeteksi Wilayah dengan kategori risiko Tinggi atau Kritis, THE Traffic_Analyzer SHALL mengestimasi dampak terhadap lalu lintas di ruas jalan yang berada dalam atau berbatasan dengan Wilayah tersebut.
2. WHEN Pengguna membuka tampilan peta pada Dashboard, THE Traffic_Analyzer SHALL menampilkan lapisan visualisasi area dengan potensi kemacetan akibat banjir, dibedakan berdasarkan tingkat keparahan (sedang, parah, tidak dapat dilalui).
3. WHEN kondisi lalu lintas di suatu ruas jalan berubah akibat banjir, THE Traffic_Analyzer SHALL memperbarui estimasi dampak lalu lintas dalam waktu tidak lebih dari 60 detik.
4. IF seluruh ruas jalan utama di suatu Wilayah teridentifikasi tidak dapat dilalui, THEN THE Traffic_Analyzer SHALL mengirimkan notifikasi isolasi wilayah kepada Pengguna dengan peran Pemerintah.

---

### Persyaratan 3: Aksesibilitas Layanan Publik

**User Story:** Sebagai pengelola rumah sakit, saya ingin mengetahui apakah fasilitas saya masih dapat diakses saat banjir, sehingga saya dapat mengkoordinasikan pengalihan pasien jika diperlukan.

#### Kriteria Penerimaan

1. WHEN Flood_Risk_Engine mendeteksi peningkatan kategori risiko banjir pada suatu Wilayah, THE Service_Accessibility_Module SHALL mengidentifikasi seluruh Fasilitas Publik yang berada dalam Wilayah terdampak beserta status aksesibilitasnya.
2. WHEN akses menuju suatu Fasilitas Publik teridentifikasi terganggu oleh Traffic_Analyzer, THE Service_Accessibility_Module SHALL menampilkan daftar Fasilitas Publik alternatif sejenis yang masih dapat diakses dalam radius 10 km.
3. WHEN kapasitas suatu Fasilitas Publik diperkirakan akan melebihi 90% akibat pengalihan pengguna, THE Service_Accessibility_Module SHALL menandai Fasilitas Publik tersebut sebagai berpotensi overload dan menyertakan informasi ini dalam rekomendasi alternatif.
4. THE Service_Accessibility_Module SHALL memperbarui status aksesibilitas seluruh Fasilitas Publik setiap 5 menit selama kondisi risiko banjir aktif.

---

### Persyaratan 4: Penilaian Risiko Terpadu (Urban Risk Score)

**User Story:** Sebagai kepala BPBD, saya ingin melihat satu indikator risiko terpadu per wilayah, sehingga saya dapat memprioritaskan alokasi sumber daya secara efisien.

#### Kriteria Penerimaan

1. WHEN Risk_Scoring_Engine menerima output dari Flood_Risk_Engine, Traffic_Analyzer, dan Service_Accessibility_Module, THE Risk_Scoring_Engine SHALL menghitung Urban Risk Score untuk setiap Wilayah dengan skala 0–100 menggunakan bobot yang dapat dikonfigurasi.
2. WHEN Dashboard dibuka oleh Pengguna, THE Risk_Scoring_Engine SHALL menampilkan visualisasi Urban Risk Score seluruh Wilayah dalam bentuk peta choropleth dengan gradasi warna berdasarkan tingkat risiko.
3. WHEN Urban Risk Score suatu Wilayah meningkat melampaui ambang batas 70, THE Risk_Scoring_Engine SHALL memicu kalkulasi ulang rekomendasi tindakan oleh Recommendation_Engine.
4. THE Risk_Scoring_Engine SHALL menyimpan riwayat Urban Risk Score setiap Wilayah dengan resolusi temporal minimal 1 jam untuk keperluan analisis tren.

---

### Persyaratan 5: Sistem Rekomendasi Tindakan

**User Story:** Sebagai petugas BPBD, saya ingin mendapatkan rekomendasi tindakan yang spesifik saat risiko tinggi terdeteksi, sehingga saya tidak perlu menganalisis data secara manual untuk menentukan langkah respons.

#### Kriteria Penerimaan

1. WHEN Urban Risk Score suatu Wilayah melampaui ambang batas 70, THE Recommendation_Engine SHALL menghasilkan rekomendasi tindakan yang spesifik dan dapat ditindaklanjuti untuk Pengguna dengan peran Pemerintah dalam waktu tidak lebih dari 30 detik.
2. WHEN Pengguna meminta navigasi dari titik asal ke tujuan melalui Dashboard, THE Recommendation_Engine SHALL menyarankan minimal satu rute alternatif yang menghindari Wilayah dengan kategori risiko Tinggi atau Kritis.
3. WHEN Service_Accessibility_Module menandai suatu Fasilitas Publik sebagai berpotensi overload, THE Recommendation_Engine SHALL menyertakan rekomendasi Fasilitas Publik alternatif dalam notifikasi yang dikirimkan kepada Pengguna terkait.
4. THE Recommendation_Engine SHALL mengklasifikasikan setiap rekomendasi berdasarkan urgensi: Segera (dalam 1 jam), Waspada (1–6 jam), dan Siaga (6–24 jam).
5. IF Recommendation_Engine tidak dapat menghasilkan rute alternatif yang aman karena seluruh jalur terdampak, THEN THE Recommendation_Engine SHALL menginformasikan kondisi tersebut kepada Pengguna beserta estimasi waktu pemulihan berdasarkan data historis.

---

### Persyaratan 6: Dashboard dan Visualisasi Interaktif

**User Story:** Sebagai masyarakat umum, saya ingin melihat kondisi risiko banjir di sekitar saya melalui antarmuka yang mudah dipahami, sehingga saya dapat membuat keputusan perjalanan yang lebih aman.

#### Kriteria Penerimaan

1. WHEN Pengguna membuka aplikasi URIS-AI melalui browser web, THE Dashboard SHALL menampilkan peta interaktif yang memuat Urban Risk Score, status lalu lintas, dan lokasi Fasilitas Publik dalam waktu tidak lebih dari 5 detik.
2. WHEN Pengguna memilih parameter Wilayah atau rentang waktu pada Dashboard, THE Dashboard SHALL memperbarui seluruh visualisasi yang relevan dalam waktu tidak lebih dari 3 detik.
3. THE Dashboard SHALL menyajikan informasi risiko dalam bahasa Indonesia dengan terminologi yang dapat dipahami oleh Pengguna non-teknis, tanpa menggunakan jargon teknis atau kode numerik tanpa penjelasan.
4. THE Dashboard SHALL dapat diakses dan digunakan sepenuhnya melalui browser web modern tanpa memerlukan instalasi perangkat lunak tambahan di sisi klien.
5. WHERE Pengguna mengakses Dashboard menggunakan perangkat mobile, THE Dashboard SHALL menampilkan tata letak responsif yang dapat digunakan pada layar dengan lebar minimal 360 piksel.
6. WHEN Pengguna memilih suatu Wilayah pada peta, THE Dashboard SHALL menampilkan panel detail yang memuat: Urban Risk Score, kategori risiko banjir, daftar Fasilitas Publik terdampak, dan rekomendasi tindakan terkait.

---

### Persyaratan 7: Integrasi Data Multi-Sumber

**User Story:** Sebagai administrator sistem, saya ingin data dari berbagai sumber terintegrasi secara otomatis, sehingga analisis URIS-AI selalu menggunakan informasi terkini tanpa intervensi manual.

#### Kriteria Penerimaan

1. THE Data_Integrator SHALL mengintegrasikan data dari minimal empat sumber: data cuaca (BMKG atau setara), data historis banjir, data jaringan transportasi, dan data lokasi Fasilitas Publik ke dalam satu repositori data terpadu.
2. WHEN data dari sumber eksternal diperbarui, THE Data_Integrator SHALL memperbarui repositori data terpadu dan memicu kalkulasi ulang analisis yang relevan dalam waktu tidak lebih dari 60 detik.
3. IF koneksi ke sumber data eksternal terputus, THEN THE Data_Integrator SHALL mencatat kejadian tersebut dalam log sistem, mempertahankan data terakhir yang valid, dan menampilkan indikator status koneksi pada Dashboard.
4. THE Data_Integrator SHALL memvalidasi format dan kelengkapan setiap data yang masuk sebelum menyimpannya ke repositori data terpadu, dan menolak data yang tidak memenuhi skema yang telah ditentukan.

---

### Persyaratan 8: Performa Sistem

**User Story:** Sebagai pengguna sistem saat kondisi darurat, saya ingin sistem tetap responsif meskipun banyak pengguna mengakses secara bersamaan, sehingga saya dapat mengandalkan informasi yang disajikan saat dibutuhkan paling kritis.

#### Kriteria Penerimaan

1. WHEN Pengguna mengajukan permintaan prediksi atau analisis melalui Dashboard, THE URIS-AI SHALL mengembalikan hasil dalam waktu tidak lebih dari 5 detik untuk 95% permintaan dalam kondisi beban normal.
2. WHILE jumlah Pengguna aktif secara bersamaan tidak melebihi 500, THE URIS-AI SHALL mempertahankan waktu respons tidak lebih dari 5 detik untuk seluruh permintaan analisis.
3. WHEN jumlah Pengguna aktif meningkat melebihi 500, THE URIS-AI SHALL melakukan penskalaan kapasitas secara otomatis menggunakan layanan Azure untuk mempertahankan ketersediaan sistem.
4. THE URIS-AI SHALL memiliki tingkat ketersediaan (uptime) minimal 99% dalam periode 30 hari kalender, tidak termasuk jendela pemeliharaan terjadwal yang telah dikomunikasikan sebelumnya.

---

### Persyaratan 9: Integrasi Cloud Azure

**User Story:** Sebagai administrator sistem, saya ingin sistem berjalan di atas infrastruktur Azure, sehingga saya dapat memanfaatkan skalabilitas dan keandalan layanan cloud untuk mendukung operasional sistem saat kondisi darurat.

#### Kriteria Penerimaan

1. THE URIS-AI SHALL menggunakan layanan Microsoft Azure sebagai platform utama untuk deployment aplikasi, pemrosesan data, dan hosting model AI.
2. WHEN model AI diperbarui oleh tim pengembang, THE URIS-AI SHALL mendukung proses deployment model baru menggunakan strategi blue-green deployment sehingga sistem utama tetap beroperasi tanpa gangguan selama proses pembaruan berlangsung.
3. THE URIS-AI SHALL menyimpan seluruh data operasional dan log sistem pada layanan penyimpanan Azure dengan kebijakan retensi data minimal 1 tahun.
4. WHEN terjadi kegagalan pada komponen utama sistem, THE URIS-AI SHALL melakukan failover otomatis ke instans cadangan dalam waktu tidak lebih dari 2 menit.

---

### Persyaratan 10: Keamanan dan Kontrol Akses

**User Story:** Sebagai administrator sistem, saya ingin akses ke fitur sensitif dibatasi berdasarkan peran pengguna, sehingga data operasional dan konfigurasi sistem tidak dapat diakses atau dimodifikasi oleh pihak yang tidak berwenang.

#### Kriteria Penerimaan

1. THE URIS-AI SHALL menerapkan kontrol akses berbasis peran (Role-Based Access Control) dengan minimal tiga peran: Masyarakat Umum, Pengelola Fasilitas, dan Pemerintah.
2. WHEN Pengguna mengakses fitur yang memerlukan autentikasi, THE URIS-AI SHALL memverifikasi identitas Pengguna sebelum memberikan akses ke fitur tersebut.
3. WHILE Pengguna dengan peran Masyarakat Umum menggunakan sistem, THE URIS-AI SHALL membatasi akses hanya pada fitur visualisasi peta, informasi risiko publik, dan navigasi rute alternatif.
4. IF Pengguna mencoba mengakses fitur di luar cakupan perannya, THEN THE URIS-AI SHALL menolak permintaan tersebut dan menampilkan pesan yang menjelaskan bahwa akses tidak diizinkan.
5. THE URIS-AI SHALL mengenkripsi seluruh komunikasi antara klien dan server menggunakan protokol TLS 1.2 atau lebih tinggi.
