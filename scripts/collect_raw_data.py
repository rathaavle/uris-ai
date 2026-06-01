#!/usr/bin/env python3
"""
Kumpulkan data mentah dari berbagai sumber untuk URIS-AI.

Sumber data:
1. BMKG API       — prakiraan cuaca per kecamatan (Jakarta + Jawa Barat)
2. PetaBencana.id — laporan banjir real-time Jakarta
3. OpenStreetMap  — jaringan jalan dan fasilitas publik via Overpass API
4. Data wilayah   — kode administrasi Indonesia (statis)

Output: data/raw/<sumber>/<nama_file>.csv + .sql
"""

import csv
import json
import os
import sys
import time
import sqlite3
import requests
from datetime import datetime, timezone
from pathlib import Path

# ── Setup path ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
RAW  = ROOT / "data" / "raw"
sys.path.insert(0, str(ROOT / "src"))

HEADERS = {"User-Agent": "URIS-AI/0.1 (urban-risk-research; contact@urisai.id)"}
TIMEOUT = 30

def log(msg): print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")
def ensure(path): path.mkdir(parents=True, exist_ok=True); return path

# ── Wilayah target ──────────────────────────────────────────────────────────
# adm4 = kode kelurahan BMKG (provinsi.kota.kecamatan.kelurahan)
WILAYAH = [
    # Jakarta Pusat
    {"adm4": "31.71.01.1001", "nama": "Gambir",           "kota": "Jakarta Pusat",  "lat": -6.1764, "lon": 106.8267},
    {"adm4": "31.71.02.1001", "nama": "Menteng",          "kota": "Jakarta Pusat",  "lat": -6.1944, "lon": 106.8294},
    {"adm4": "31.71.03.1001", "nama": "Tanah Abang",      "kota": "Jakarta Pusat",  "lat": -6.1867, "lon": 106.8133},
    {"adm4": "31.71.04.1001", "nama": "Kemayoran",        "kota": "Jakarta Pusat",  "lat": -6.1667, "lon": 106.8500},
    # Jakarta Utara
    {"adm4": "31.72.01.1001", "nama": "Penjaringan",      "kota": "Jakarta Utara",  "lat": -6.1167, "lon": 106.7833},
    {"adm4": "31.72.02.1001", "nama": "Pademangan",       "kota": "Jakarta Utara",  "lat": -6.1333, "lon": 106.8333},
    {"adm4": "31.72.03.1001", "nama": "Kelapa Gading",    "kota": "Jakarta Utara",  "lat": -6.1578, "lon": 106.9097},
    # Jakarta Barat
    {"adm4": "31.73.01.1001", "nama": "Cengkareng",       "kota": "Jakarta Barat",  "lat": -6.1500, "lon": 106.7333},
    {"adm4": "31.73.02.1001", "nama": "Kebon Jeruk",      "kota": "Jakarta Barat",  "lat": -6.1833, "lon": 106.7667},
    {"adm4": "31.73.03.1001", "nama": "Grogol Petamburan","kota": "Jakarta Barat",  "lat": -6.1667, "lon": 106.7833},
    # Jakarta Selatan
    {"adm4": "31.74.01.1001", "nama": "Kebayoran Baru",   "kota": "Jakarta Selatan","lat": -6.2425, "lon": 106.7972},
    {"adm4": "31.74.02.1001", "nama": "Tebet",            "kota": "Jakarta Selatan","lat": -6.2333, "lon": 106.8500},
    {"adm4": "31.74.03.1001", "nama": "Cilandak",         "kota": "Jakarta Selatan","lat": -6.2917, "lon": 106.8000},
    # Jakarta Timur
    {"adm4": "31.75.01.1001", "nama": "Matraman",         "kota": "Jakarta Timur",  "lat": -6.2000, "lon": 106.8667},
    {"adm4": "31.75.02.1001", "nama": "Jatinegara",       "kota": "Jakarta Timur",  "lat": -6.2167, "lon": 106.8667},
    {"adm4": "31.75.03.1001", "nama": "Cakung",           "kota": "Jakarta Timur",  "lat": -6.1667, "lon": 106.9333},
    # Jawa Barat
    {"adm4": "32.73.01.1001", "nama": "Bandung Wetan",    "kota": "Kota Bandung",   "lat": -6.9175, "lon": 107.6191},
    {"adm4": "32.73.02.1001", "nama": "Cicendo",          "kota": "Kota Bandung",   "lat": -6.9147, "lon": 107.5931},
    {"adm4": "32.73.03.1001", "nama": "Coblong",          "kota": "Kota Bandung",   "lat": -6.8722, "lon": 107.6069},
    {"adm4": "32.71.01.1001", "nama": "Bogor Tengah",     "kota": "Kota Bogor",     "lat": -6.5950, "lon": 106.7969},
    {"adm4": "32.71.02.1001", "nama": "Bogor Utara",      "kota": "Kota Bogor",     "lat": -6.5700, "lon": 106.8000},
    {"adm4": "32.71.03.1001", "nama": "Tanah Sareal",     "kota": "Kota Bogor",     "lat": -6.5833, "lon": 106.7833},
    {"adm4": "32.75.01.1001", "nama": "Bekasi Timur",     "kota": "Kota Bekasi",    "lat": -6.2500, "lon": 107.0167},
    {"adm4": "32.75.02.1001", "nama": "Bekasi Barat",     "kota": "Kota Bekasi",    "lat": -6.2333, "lon": 106.9833},
    {"adm4": "32.76.01.1001", "nama": "Depok",            "kota": "Kota Depok",     "lat": -6.4000, "lon": 106.8186},
]


# ════════════════════════════════════════════════════════════════════════════
# 1. BMKG — Prakiraan Cuaca
# ════════════════════════════════════════════════════════════════════════════
def fetch_bmkg():
    log("=== BMKG: Mengambil prakiraan cuaca ===")
    out_dir = ensure(RAW / "bmkg")
    rows = []
    fetched_at = datetime.now(timezone.utc).isoformat()

    for w in WILAYAH:
        url = f"https://api.bmkg.go.id/publik/prakiraan-cuaca?adm4={w['adm4']}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            data = r.json()
            cuaca_list = data.get("data", [{}])[0].get("cuaca", [])
            for day_group in cuaca_list:
                for item in day_group:
                    rows.append({
                        "adm4":          w["adm4"],
                        "wilayah":       w["nama"],
                        "kota":          w["kota"],
                        "lat":           w["lat"],
                        "lon":           w["lon"],
                        "datetime_utc":  item.get("datetime", ""),
                        "local_datetime":item.get("local_datetime", ""),
                        "suhu_c":        item.get("t", ""),
                        "kelembaban_pct":item.get("hu", ""),
                        "curah_hujan_mm":item.get("tp", ""),
                        "kecepatan_angin_ms": item.get("ws", ""),
                        "arah_angin":    item.get("wd", ""),
                        "tutupan_awan_pct": item.get("tcc", ""),
                        "jarak_pandang_m":  item.get("vs", ""),
                        "cuaca_kode":    item.get("weather", ""),
                        "cuaca_desc":    item.get("weather_desc", ""),
                        "fetched_at":    fetched_at,
                    })
            log(f"  ✓ {w['nama']} ({len(cuaca_list)} hari)")
            time.sleep(0.3)
        except Exception as e:
            log(f"  ✗ {w['nama']}: {e}")

    if not rows:
        log("  Tidak ada data BMKG yang berhasil diambil.")
        return

    # CSV
    csv_path = out_dir / "prakiraan_cuaca.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    log(f"  → CSV: {csv_path} ({len(rows)} baris)")

    # SQL
    sql_path = out_dir / "prakiraan_cuaca.sql"
    _write_sql(sql_path, "bmkg_prakiraan_cuaca", rows)
    log(f"  → SQL: {sql_path}")


# ════════════════════════════════════════════════════════════════════════════
# 2. PetaBencana.id — Laporan Banjir Real-time
# ════════════════════════════════════════════════════════════════════════════
def fetch_petabencana():
    log("=== PetaBencana.id: Mengambil laporan banjir ===")
    out_dir = ensure(RAW / "petabencana")
    fetched_at = datetime.now(timezone.utc).isoformat()
    rows = []

    # Flood reports untuk DKI Jakarta (city code: jbd)
    url = "https://data.petabencana.id/floods?city=jbd&minimum_state=1"
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json()
        features = data.get("result", {}).get("features", [])
        for feat in features:
            props = feat.get("properties", {})
            geom  = feat.get("geometry", {})
            coords = geom.get("coordinates", [None, None]) if geom else [None, None]
            rows.append({
                "flood_id":      props.get("pkey", ""),
                "area_id":       props.get("area_id", ""),
                "area_name":     props.get("area_name", ""),
                "city":          props.get("city", "jbd"),
                "state":         props.get("state", ""),
                "last_updated":  props.get("last_updated", ""),
                "lon":           coords[0] if coords else "",
                "lat":           coords[1] if coords else "",
                "fetched_at":    fetched_at,
            })
        log(f"  ✓ {len(rows)} area banjir aktif (Jakarta)")
    except Exception as e:
        log(f"  ✗ Flood reports: {e}")

    # Flood gauges (tinggi muka air)
    url2 = "https://data.petabencana.id/floodgauges?city=jbd"
    try:
        r2 = requests.get(url2, headers=HEADERS, timeout=TIMEOUT)
        r2.raise_for_status()
        data2 = r2.json()
        gauge_rows = []
        features2 = data2.get("result", {}).get("features", [])
        for feat in features2:
            props = feat.get("properties", {})
            geom  = feat.get("geometry", {})
            coords = geom.get("coordinates", [None, None]) if geom else [None, None]
            gauge_rows.append({
                "gauge_id":      props.get("gauge_id", ""),
                "gauge_name":    props.get("gauge_name", ""),
                "city":          "jbd",
                "water_depth_m": props.get("observations", [{}])[-1].get("depth", "") if props.get("observations") else "",
                "last_observed": props.get("observations", [{}])[-1].get("timestamp", "") if props.get("observations") else "",
                "lon":           coords[0] if coords else "",
                "lat":           coords[1] if coords else "",
                "fetched_at":    fetched_at,
            })
        if gauge_rows:
            gauge_csv = out_dir / "flood_gauges.csv"
            with open(gauge_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=gauge_rows[0].keys())
                writer.writeheader()
                writer.writerows(gauge_rows)
            _write_sql(out_dir / "flood_gauges.sql", "petabencana_flood_gauges", gauge_rows)
            log(f"  ✓ {len(gauge_rows)} gauge air → flood_gauges.csv")
    except Exception as e:
        log(f"  ✗ Flood gauges: {e}")

    if rows:
        csv_path = out_dir / "flood_reports.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        _write_sql(out_dir / "flood_reports.sql", "petabencana_flood_reports", rows)
        log(f"  → CSV: {csv_path}")
    else:
        log("  Info: Tidak ada banjir aktif saat ini (data tetap disimpan kosong)")
        _write_empty_csv(out_dir / "flood_reports.csv",
            ["flood_id","area_id","area_name","city","state","last_updated","lon","lat","fetched_at"])


# ════════════════════════════════════════════════════════════════════════════
# 3. OpenStreetMap — Jalan & Fasilitas Publik via Overpass API
# ════════════════════════════════════════════════════════════════════════════
OVERPASS_URL = "https://overpass-api.de/api/interpreter"

def overpass_query(query: str) -> dict:
    r = requests.post(OVERPASS_URL, data={"data": query}, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.json()

def fetch_osm():
    log("=== OpenStreetMap: Mengambil data jalan & fasilitas ===")
    out_dir = ensure(RAW / "osm")
    fetched_at = datetime.now(timezone.utc).isoformat()

    # Bounding box: Jakarta + Jawa Barat
    BBOX = "-7.0,106.5,-6.0,107.2"  # south,west,north,east

    # 3a. Jalan utama Jakarta
    log("  Mengambil data jalan utama Jakarta...")
    road_query = f"""
[out:json][timeout:60];
(
  way["highway"~"^(motorway|trunk|primary|secondary)$"]({BBOX});
);
out body; >; out skel qt;
"""
    road_rows = []
    try:
        data = overpass_query(road_query)
        for el in data.get("elements", []):
            if el.get("type") == "way":
                tags = el.get("tags", {})
                road_rows.append({
                    "osm_id":       el.get("id", ""),
                    "road_name":    tags.get("name", ""),
                    "road_name_en": tags.get("name:en", ""),
                    "highway_type": tags.get("highway", ""),
                    "oneway":       tags.get("oneway", "no"),
                    "lanes":        tags.get("lanes", ""),
                    "maxspeed":     tags.get("maxspeed", ""),
                    "surface":      tags.get("surface", ""),
                    "node_count":   len(el.get("nodes", [])),
                    "fetched_at":   fetched_at,
                })
        log(f"  ✓ {len(road_rows)} ruas jalan")
        time.sleep(2)
    except Exception as e:
        log(f"  ✗ Jalan: {e}")

    if road_rows:
        csv_path = out_dir / "roads.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=road_rows[0].keys())
            writer.writeheader()
            writer.writerows(road_rows)
        _write_sql(out_dir / "roads.sql", "osm_roads", road_rows)
        log(f"  → CSV: {csv_path}")

    # 3b. Fasilitas kesehatan
    log("  Mengambil fasilitas kesehatan...")
    health_query = f"""
[out:json][timeout:60];
(
  node["amenity"~"^(hospital|clinic|doctors|pharmacy|health_post)$"]({BBOX});
  way["amenity"~"^(hospital|clinic|doctors|pharmacy|health_post)$"]({BBOX});
);
out center body qt;
"""
    health_rows = []
    try:
        data = overpass_query(health_query)
        for el in data.get("elements", []):
            tags = el.get("tags", {})
            lat = el.get("lat") or el.get("center", {}).get("lat", "")
            lon = el.get("lon") or el.get("center", {}).get("lon", "")
            health_rows.append({
                "osm_id":       el.get("id", ""),
                "osm_type":     el.get("type", ""),
                "name":         tags.get("name", ""),
                "amenity":      tags.get("amenity", ""),
                "operator":     tags.get("operator", ""),
                "beds":         tags.get("beds", ""),
                "emergency":    tags.get("emergency", ""),
                "phone":        tags.get("phone", ""),
                "opening_hours":tags.get("opening_hours", ""),
                "lat":          lat,
                "lon":          lon,
                "fetched_at":   fetched_at,
            })
        log(f"  ✓ {len(health_rows)} fasilitas kesehatan")
        time.sleep(2)
    except Exception as e:
        log(f"  ✗ Fasilitas kesehatan: {e}")

    if health_rows:
        csv_path = out_dir / "fasilitas_kesehatan.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=health_rows[0].keys())
            writer.writeheader()
            writer.writerows(health_rows)
        _write_sql(out_dir / "fasilitas_kesehatan.sql", "osm_fasilitas_kesehatan", health_rows)
        log(f"  → CSV: {csv_path}")

    # 3c. Sekolah & kantor pemerintah
    log("  Mengambil sekolah & kantor pemerintah...")
    gov_query = f"""
[out:json][timeout:60];
(
  node["amenity"~"^(school|university|government|townhall|fire_station|police)$"]({BBOX});
  way["amenity"~"^(school|university|government|townhall|fire_station|police)$"]({BBOX});
);
out center body qt;
"""
    gov_rows = []
    try:
        data = overpass_query(gov_query)
        for el in data.get("elements", []):
            tags = el.get("tags", {})
            lat = el.get("lat") or el.get("center", {}).get("lat", "")
            lon = el.get("lon") or el.get("center", {}).get("lon", "")
            gov_rows.append({
                "osm_id":    el.get("id", ""),
                "osm_type":  el.get("type", ""),
                "name":      tags.get("name", ""),
                "amenity":   tags.get("amenity", ""),
                "operator":  tags.get("operator", ""),
                "lat":       lat,
                "lon":       lon,
                "fetched_at": fetched_at,
            })
        log(f"  ✓ {len(gov_rows)} fasilitas publik lainnya")
        time.sleep(2)
    except Exception as e:
        log(f"  ✗ Fasilitas publik: {e}")

    if gov_rows:
        csv_path = out_dir / "fasilitas_publik.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=gov_rows[0].keys())
            writer.writeheader()
            writer.writerows(gov_rows)
        _write_sql(out_dir / "fasilitas_publik.sql", "osm_fasilitas_publik", gov_rows)
        log(f"  → CSV: {csv_path}")


# ════════════════════════════════════════════════════════════════════════════
# 4. Data Wilayah Administrasi (statis)
# ════════════════════════════════════════════════════════════════════════════
def fetch_wilayah():
    log("=== Data Wilayah: Menyimpan data administrasi ===")
    out_dir = ensure(RAW / "wilayah")
    fetched_at = datetime.now(timezone.utc).isoformat()

    rows = []
    for i, w in enumerate(WILAYAH, start=1):
        rows.append({
            "region_id":   i,
            "adm4":        w["adm4"],
            "adm3":        ".".join(w["adm4"].split(".")[:3]),
            "adm2":        ".".join(w["adm4"].split(".")[:2]),
            "adm1":        w["adm4"].split(".")[0],
            "nama_wilayah": w["nama"],
            "kota":        w["kota"],
            "provinsi":    "DKI Jakarta" if w["adm4"].startswith("31") else "Jawa Barat",
            "lat":         w["lat"],
            "lon":         w["lon"],
            "fetched_at":  fetched_at,
        })

    csv_path = out_dir / "wilayah_administrasi.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    _write_sql(out_dir / "wilayah_administrasi.sql", "wilayah_administrasi", rows)
    log(f"  ✓ {len(rows)} wilayah → {csv_path}")


# ════════════════════════════════════════════════════════════════════════════
# 5. Data Historis Banjir Jakarta (dari dataset publik)
# ════════════════════════════════════════════════════════════════════════════
def fetch_historis_banjir():
    """
    Data historis banjir Jakarta dari PetaBencana archive API.
    Mengambil laporan 7 hari terakhir sebagai baseline historis.
    """
    log("=== Historis Banjir: Mengambil archive laporan banjir ===")
    out_dir = ensure(RAW / "historis_banjir")
    fetched_at = datetime.now(timezone.utc).isoformat()
    rows = []

    # PetaBencana archive — laporan banjir per kecamatan Jakarta
    cities = ["jbd"]  # Jakarta
    for city in cities:
        url = f"https://data.petabencana.id/floods/archive?city={city}&format=json"
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            data = r.json()
            features = data.get("result", {}).get("features", [])
            for feat in features:
                props = feat.get("properties", {})
                geom  = feat.get("geometry", {})
                coords = geom.get("coordinates", [None, None]) if geom else [None, None]
                rows.append({
                    "report_id":    props.get("pkey", ""),
                    "city":         city,
                    "area_id":      props.get("area_id", ""),
                    "area_name":    props.get("area_name", ""),
                    "flood_state":  props.get("state", ""),
                    "report_time":  props.get("created_at", ""),
                    "last_updated": props.get("last_updated", ""),
                    "lon":          coords[0] if coords else "",
                    "lat":          coords[1] if coords else "",
                    "fetched_at":   fetched_at,
                })
            log(f"  ✓ {len(rows)} laporan historis ({city})")
            time.sleep(1)
        except Exception as e:
            log(f"  ✗ Archive {city}: {e}")

    if rows:
        csv_path = out_dir / "historis_banjir_jakarta.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
        _write_sql(out_dir / "historis_banjir_jakarta.sql",
                   "historis_banjir_jakarta", rows)
        log(f"  → CSV: {csv_path} ({len(rows)} baris)")
    else:
        log("  Info: Tidak ada data archive tersedia, membuat file kosong")
        _write_empty_csv(out_dir / "historis_banjir_jakarta.csv",
            ["report_id","city","area_id","area_name","flood_state",
             "report_time","last_updated","lon","lat","fetched_at"])


# ════════════════════════════════════════════════════════════════════════════
# Helper: tulis SQL INSERT statements
# ════════════════════════════════════════════════════════════════════════════
def _write_sql(path: Path, table: str, rows: list):
    if not rows:
        return
    cols = list(rows[0].keys())
    col_defs = ", ".join(f'"{c}" TEXT' for c in cols)
    lines = [
        f"-- Generated by collect_raw_data.py on {datetime.now().isoformat()}",
        f"-- Source table: {table}",
        f"",
        f'CREATE TABLE IF NOT EXISTS "{table}" ({col_defs});',
        f"",
    ]
    for row in rows:
        vals = ", ".join(
            "NULL" if (v == "" or v is None)
            else "'" + str(v).replace("'", "''") + "'"
            for v in row.values()
        )
        lines.append(f'INSERT INTO "{table}" VALUES ({vals});')
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def _write_empty_csv(path: Path, fieldnames: list):
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()


# ════════════════════════════════════════════════════════════════════════════
# Buat SQLite database gabungan
# ════════════════════════════════════════════════════════════════════════════
def build_sqlite_db():
    log("=== Membangun SQLite database gabungan ===")
    db_path = RAW / "uris_ai_raw.db"
    conn = sqlite3.connect(db_path)

    sql_files = list(RAW.rglob("*.sql"))
    loaded = 0
    for sql_file in sorted(sql_files):
        try:
            sql_text = sql_file.read_text(encoding="utf-8")
            conn.executescript(sql_text)
            loaded += 1
            log(f"  ✓ {sql_file.relative_to(RAW)}")
        except Exception as e:
            log(f"  ✗ {sql_file.name}: {e}")

    conn.commit()
    conn.close()
    log(f"  → SQLite DB: {db_path} ({loaded} file SQL dimuat)")


# ════════════════════════════════════════════════════════════════════════════
# Main
# ════════════════════════════════════════════════════════════════════════════
def main():
    log("╔══════════════════════════════════════════════════╗")
    log("║  URIS-AI — Pengumpulan Data Mentah               ║")
    log("╚══════════════════════════════════════════════════╝")
    log(f"Output: {RAW}")
    log("")

    fetch_wilayah()
    log("")
    fetch_bmkg()
    log("")
    fetch_petabencana()
    log("")
    fetch_historis_banjir()
    log("")
    fetch_osm()
    log("")
    build_sqlite_db()

    log("")
    log("╔══════════════════════════════════════════════════╗")
    log("║  SELESAI — Ringkasan file yang dihasilkan:       ║")
    log("╚══════════════════════════════════════════════════╝")
    for f in sorted(RAW.rglob("*")):
        if f.is_file() and f.suffix in (".csv", ".sql", ".db"):
            size_kb = f.stat().st_size // 1024
            log(f"  {f.relative_to(RAW)}  ({size_kb} KB)")


if __name__ == "__main__":
    main()
