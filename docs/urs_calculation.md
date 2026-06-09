# Urban Risk Score (URS) — Penjelasan Perhitungan

## Formula Utama

```
URS = (Flood Risk × 50%) + (Traffic Impact × 30%) + (Service Access × 20%)
```

---

## 1. Flood Risk (bobot 50%)

Dihitung dari tiga faktor geografis:

```
Flood Risk = elev_score + drain_score + coast_score
```

| Komponen                           | Rentang   | Logika                                                              |
| ---------------------------------- | --------- | ------------------------------------------------------------------- |
| `elev_score` (Elevasi)             | 0–40 poin | `(25 - elevasi) × 1.6` — elevasi rendah = risiko tinggi             |
| `drain_score` (Kapasitas Drainase) | 0–30 poin | `(200 - drainage_capacity) × 0.15` — drainase buruk = risiko tinggi |
| `coast_score` (Jarak ke Pantai)    | 0–20 poin | `(30 - jarak_pantai) × 0.67` — dekat pantai = risiko tinggi         |

Hasil akhir di-clamp ke rentang **5–95**.

---

## 2. Traffic Impact (bobot 30%)

```
Traffic Impact = Flood Risk × 0.65 × city_factor
```

| Komponen      | Keterangan                                            |
| ------------- | ----------------------------------------------------- |
| `Flood Risk`  | Basis utama                                           |
| `city_factor` | Pengali per kota: Jakarta Utara `1.1` → Bandung `0.7` |

---

## 3. Service Access (bobot 20%)

```
Service Access = Flood Risk × 0.42
```

Merepresentasikan kemudahan akses ke fasilitas publik (rumah sakit, dll.) saat kondisi banjir.

---

## Hierarki Variabel

```
Urban Risk Score
├── Flood Risk (50%)
│   ├── Elevasi              [0–40 poin]
│   ├── Drainage Capacity    [0–30 poin]
│   └── Jarak ke Pantai      [0–20 poin]
│
├── Traffic Impact (30%)
│   └── Flood Risk × city_factor
│
└── Service Access (20%)
    └── Flood Risk × 0.42
```

> **Catatan:** Traffic Impact dan Service Access keduanya merupakan turunan dari Flood Risk,
> sehingga Flood Risk menjadi akar dari seluruh perhitungan URS.

---

## Kategori URS

| Rentang Skor | Kategori  |
| ------------ | --------- |
| 0 – 25       | 🟢 RENDAH |
| 26 – 50      | 🟡 SEDANG |
| 51 – 75      | 🟠 TINGGI |
| 76 – 100     | 🔴 KRITIS |
