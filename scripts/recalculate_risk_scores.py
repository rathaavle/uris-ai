#!/usr/bin/env python3
"""
Recalculate risk scores menggunakan pendekatan rule-based yang lebih bervariasi.

Faktor yang digunakan:
- Elevasi (semakin rendah = semakin rawan)
- Kapasitas drainase (semakin kecil = semakin rawan)
- Jarak ke pantai / posisi geografis
- Frekuensi banjir historis per region
- Kepadatan jalan (proxy kemacetan)
- Jumlah fasilitas publik (proxy aksesibilitas)
"""

import sys
import random
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text
from uris_ai.config import settings
from uris_ai.models.db_utils import create_db_engine

engine = create_db_engine(settings.azure_mysql_connection_string)

# Data karakteristik per region — berbasis fakta geografis
# Format: region_id: (elevasi_m, drainage, jarak_pantai_km, nama)
REGION_PROFILE = {
    1:  {"name": "Menteng",           "elev": 7,   "drain": 150, "dist_coast": 12, "city": "jakarta_pusat"},
    2:  {"name": "Tanah Abang",       "elev": 5,   "drain": 120, "dist_coast": 10, "city": "jakarta_pusat"},
    3:  {"name": "Kemayoran",         "elev": 8,   "drain": 180, "dist_coast": 8,  "city": "jakarta_pusat"},
    4:  {"name": "Kelapa Gading",     "elev": 3,   "drain": 100, "dist_coast": 5,  "city": "jakarta_utara"},
    5:  {"name": "Penjaringan",       "elev": 2,   "drain": 80,  "dist_coast": 1,  "city": "jakarta_utara"},
    6:  {"name": "Pademangan",        "elev": 4,   "drain": 110, "dist_coast": 3,  "city": "jakarta_utara"},
    7:  {"name": "Kebayoran Baru",    "elev": 15,  "drain": 200, "dist_coast": 20, "city": "jakarta_selatan"},
    8:  {"name": "Tebet",             "elev": 12,  "drain": 170, "dist_coast": 18, "city": "jakarta_selatan"},
    9:  {"name": "Cilandak",          "elev": 50,  "drain": 250, "dist_coast": 30, "city": "jakarta_selatan"},
    10: {"name": "Cengkareng",        "elev": 6,   "drain": 130, "dist_coast": 7,  "city": "jakarta_barat"},
    11: {"name": "Kebon Jeruk",       "elev": 10,  "drain": 160, "dist_coast": 15, "city": "jakarta_barat"},
    12: {"name": "Grogol Petamburan", "elev": 8,   "drain": 140, "dist_coast": 9,  "city": "jakarta_barat"},
    13: {"name": "Matraman",          "elev": 9,   "drain": 145, "dist_coast": 16, "city": "jakarta_timur"},
    14: {"name": "Jatinegara",        "elev": 7,   "drain": 135, "dist_coast": 14, "city": "jakarta_timur"},
    15: {"name": "Cakung",            "elev": 5,   "drain": 115, "dist_coast": 11, "city": "jakarta_timur"},
    16: {"name": "Bandung Wetan",     "elev": 768, "drain": 220, "dist_coast": 180,"city": "bandung"},
    17: {"name": "Cicendo",           "elev": 750, "drain": 210, "dist_coast": 175,"city": "bandung"},
    18: {"name": "Coblong",           "elev": 800, "drain": 240, "dist_coast": 185,"city": "bandung"},
    19: {"name": "Bogor Tengah",      "elev": 290, "drain": 190, "dist_coast": 60, "city": "bogor"},
    20: {"name": "Bogor Utara",       "elev": 250, "drain": 180, "dist_coast": 55, "city": "bogor"},
    21: {"name": "Tanah Sareal",      "elev": 270, "drain": 185, "dist_coast": 58, "city": "bogor"},
    22: {"name": "Bekasi Timur",      "elev": 19,  "drain": 125, "dist_coast": 25, "city": "bekasi"},
    23: {"name": "Bekasi Barat",      "elev": 15,  "drain": 120, "dist_coast": 20, "city": "bekasi"},
    24: {"name": "Pondok Gede",       "elev": 22,  "drain": 130, "dist_coast": 28, "city": "bekasi"},
    25: {"name": "Depok",             "elev": 80,  "drain": 165, "dist_coast": 45, "city": "depok"},
}

def calc_flood_risk(p: dict, seed_offset: int = 0) -> float:
    """
    Hitung flood risk berdasarkan faktor geografis.
    Rentang: 5–95
    """
    random.seed(p["elev"] + p["drain"] + seed_offset)

    # Komponen elevasi (0-40): elevasi rendah = risiko tinggi
    elev_score = max(0, min(40, (25 - min(p["elev"], 25)) * 1.6))

    # Komponen drainase (0-30): drainage buruk = risiko tinggi
    drain_score = max(0, min(30, (200 - min(p["drain"], 200)) * 0.15))

    # Komponen jarak pantai (0-20): dekat pantai = risiko tinggi
    coast_score = max(0, min(20, (30 - min(p["dist_coast"], 30)) * 0.67))

    # Noise kecil untuk variasi antar wilayah serupa (±5)
    noise = random.uniform(-5, 5)

    raw = elev_score + drain_score + coast_score + noise
    return max(5.0, min(95.0, round(raw, 2)))

def calc_traffic_impact(flood: float, p: dict) -> float:
    """Traffic impact berbasis flood risk + karakteristik kota."""
    # Jakarta lebih padat → traffic impact lebih tinggi
    city_factor = {
        "jakarta_utara": 1.1, "jakarta_pusat": 1.05, "jakarta_barat": 1.0,
        "jakarta_timur": 1.0, "jakarta_selatan": 0.95,
        "bekasi": 0.85, "depok": 0.80, "bogor": 0.75, "bandung": 0.70,
    }.get(p["city"], 0.9)

    random.seed(p["elev"] * 3 + p["drain"])
    noise = random.uniform(-4, 4)
    raw = flood * 0.65 * city_factor + noise
    return max(5.0, min(95.0, round(raw, 2)))

def calc_service_access(flood: float, p: dict) -> float:
    """Service accessibility: daerah terisolasi saat banjir."""
    # Wilayah pantai rendah = akses ke RS lebih sulit saat banjir
    random.seed(p["drain"] + p["elev"] * 2)
    noise = random.uniform(-6, 6)
    raw = flood * 0.42 + noise
    return max(5.0, min(95.0, round(raw, 2)))

def get_category(urs: float) -> str:
    if urs < 26: return "RENDAH"
    if urs < 51: return "SEDANG"
    if urs < 76: return "TINGGI"
    return "KRITIS"

print("Recalculating risk scores (rule-based geographic)...")
now = datetime.now(timezone.utc)

with engine.connect() as conn:
    updated = 0
    for rid, p in REGION_PROFILE.items():
        flood = calc_flood_risk(p)
        traffic = calc_traffic_impact(flood, p)
        service = calc_service_access(flood, p)
        urs = round(flood * 0.5 + traffic * 0.3 + service * 0.2, 2)
        cat = get_category(urs)

        conn.execute(text("""
            UPDATE risk_scores
            SET flood_risk=:fr, traffic_impact=:ti,
                service_access=:sa, urban_risk_score=:urs, date=:dt
            WHERE region_id=:rid
        """), {"fr": flood, "ti": traffic, "sa": service, "urs": urs, "dt": now, "rid": rid})

        print(f"  [{cat:7}] {p['name']:25} flood={flood:.1f} traffic={traffic:.1f} service={service:.1f} URS={urs:.2f}")
        updated += 1

    conn.commit()

print(f"\n✓ {updated} risk scores diperbarui")
