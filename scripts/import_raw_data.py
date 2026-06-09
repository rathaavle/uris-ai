#!/usr/bin/env python3
"""
Task 22 — Import data raw ke Azure MySQL.

Import dari data/raw/ CSV ke tabel MySQL:
- wilayah_administrasi.csv  → regions (upsert)
- prakiraan_cuaca.csv       → weather_data
- historis_banjir_jakarta.csv → flood_events (jika ada)
- fasilitas_kesehatan.csv   → public_facilities
- fasilitas_publik.csv      → public_facilities
- roads.csv                 → roads

Usage:
    python scripts/import_raw_data.py [--reset]
"""

import sys
import csv
import logging
import argparse
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy.orm import Session
from uris_ai.config import settings
from uris_ai.models.db_utils import create_db_engine, create_session_factory
from uris_ai.models.database import (
    Base, Region, WeatherData, FloodEvent, Road, PublicFacility
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

RAW = Path(__file__).parent.parent / "data" / "raw"

# Map kota → region_id dari seed data
KOTA_TO_REGION = {
    "gambir":           1,
    "menteng":          2,
    "tanah abang":      3,
    "kemayoran":        4,
    "penjaringan":      5,
    "pademangan":       6,
    "kelapa gading":    4,
    "kebayoran baru":   7,
    "tebet":            8,
    "cilandak":         9,
    "cengkareng":       10,
    "kebon jeruk":      11,
    "grogol petamburan":12,
    "matraman":         13,
    "jatinegara":       14,
    "cakung":           15,
    "bandung wetan":    16,
    "cicendo":          17,
    "coblong":          18,
    "bogor tengah":     19,
    "bogor utara":      20,
    "tanah sareal":     21,
    "bekasi timur":     22,
    "bekasi barat":     23,
    "pondok gede":      24,
    "depok":            25,
}

def find_region_id(nama: str, kota: str) -> int | None:
    """Cari region_id berdasarkan nama wilayah atau kota."""
    nama_lower = nama.lower()
    for key, rid in KOTA_TO_REGION.items():
        if key in nama_lower:
            return rid
    kota_lower = kota.lower()
    for key, rid in KOTA_TO_REGION.items():
        if key in kota_lower:
            return rid
    return None

def safe_float(val, default=0.0):
    try:
        return float(val) if val not in ("", None) else default
    except (ValueError, TypeError):
        return default

def safe_int(val, default=0):
    try:
        return int(float(val)) if val not in ("", None) else default
    except (ValueError, TypeError):
        return default


# ── 1. Import wilayah administrasi ───────────────────────────────────
def import_wilayah(session: Session, reset: bool = False) -> int:
    log.info("=== Import: Wilayah Administrasi ===")
    csv_path = RAW / "wilayah" / "wilayah_administrasi.csv"
    if not csv_path.exists():
        log.warning(f"  File tidak ditemukan: {csv_path}")
        return 0

    count = 0
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rid = safe_int(row.get("region_id"))
            existing = session.query(Region).filter(Region.region_id == rid).first()
            if existing:
                # Upsert — update koordinat jika berbeda
                existing.name = row.get("nama_wilayah", existing.name)
                existing.latitude = safe_float(row.get("lat"), existing.latitude)
                existing.longitude = safe_float(row.get("lon"), existing.longitude)
            else:
                region = Region(
                    region_id=rid,
                    name=row.get("nama_wilayah", ""),
                    latitude=safe_float(row.get("lat")),
                    longitude=safe_float(row.get("lon")),
                )
                session.add(region)
            count += 1

    session.commit()
    log.info(f"  ✓ {count} wilayah di-upsert")
    return count


# ── 2. Import prakiraan cuaca BMKG ────────────────────────────────────
def import_weather(session: Session, reset: bool = False) -> int:
    log.info("=== Import: Prakiraan Cuaca BMKG ===")
    csv_path = RAW / "bmkg" / "prakiraan_cuaca.csv"
    if not csv_path.exists():
        log.warning(f"  File tidak ditemukan: {csv_path}")
        return 0

    if reset:
        deleted = session.query(WeatherData).delete()
        session.commit()
        log.info(f"  Reset: {deleted} baris dihapus")

    existing_count = session.query(WeatherData).count()
    if existing_count > 0 and not reset:
        log.info(f"  Skip: sudah ada {existing_count} baris. Gunakan --reset untuk reimport.")
        return 0

    count = 0
    skipped = 0
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            wilayah = row.get("wilayah", "")
            kota = row.get("kota", "")
            region_id = find_region_id(wilayah, kota)
            if not region_id:
                skipped += 1
                continue

            dt_str = row.get("local_datetime", "") or row.get("datetime_utc", "")
            try:
                dt = datetime.fromisoformat(dt_str.replace(" ", "T")) if dt_str else datetime.now()
            except ValueError:
                dt = datetime.now()

            wd = WeatherData(
                region_id=region_id,
                date=dt,
                rainfall=safe_float(row.get("curah_hujan_mm")),
                humidity=safe_float(row.get("kelembaban_pct")),
                temperature=safe_float(row.get("suhu_c")),
                wind_speed=safe_float(row.get("kecepatan_angin_ms")),
            )
            session.add(wd)
            count += 1

            if count % 100 == 0:
                session.flush()

    session.commit()
    log.info(f"  ✓ {count} baris cuaca diimport, {skipped} dilewati (region tidak ditemukan)")
    return count


# ── 3. Import fasilitas kesehatan ─────────────────────────────────────
def import_facilities(session: Session, reset: bool = False) -> int:
    log.info("=== Import: Fasilitas (Kesehatan + Publik) ===")

    if reset:
        deleted = session.query(PublicFacility).delete()
        session.commit()
        log.info(f"  Reset: {deleted} fasilitas dihapus")

    existing_count = session.query(PublicFacility).count()
    if existing_count > 0 and not reset:
        log.info(f"  Skip: sudah ada {existing_count} fasilitas. Gunakan --reset untuk reimport.")
        return 0

    total = 0

    for fname, ftype_default in [
        ("fasilitas_kesehatan.csv", "hospital"),
        ("fasilitas_publik.csv", "government"),
    ]:
        csv_path = RAW / "osm" / fname
        if not csv_path.exists():
            log.warning(f"  File tidak ditemukan: {csv_path}")
            continue

        count = 0
        skipped = 0
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                lat = safe_float(row.get("lat"))
                lon = safe_float(row.get("lon"))
                if not lat or not lon:
                    skipped += 1
                    continue

                # Cari region_id berdasarkan kota
                city = row.get("city", "")
                region_id = find_region_id(city, city)
                if not region_id:
                    # Fallback: assign ke region terdekat berdasarkan kota
                    city_lower = city.lower()
                    if "jakarta" in city_lower:
                        region_id = 5  # Penjaringan sebagai default Jakarta
                    elif "bandung" in city_lower:
                        region_id = 16
                    elif "bogor" in city_lower:
                        region_id = 19
                    elif "bekasi" in city_lower:
                        region_id = 22
                    elif "depok" in city_lower:
                        region_id = 25
                    else:
                        skipped += 1
                        continue

                amenity = row.get("amenity", ftype_default) or ftype_default
                name = row.get("name", "") or f"{amenity} #{row.get('osm_id','')}"

                fac = PublicFacility(
                    region_id=region_id,
                    name=name[:255],
                    type=amenity[:50],
                    latitude=lat,
                    longitude=lon,
                    is_operational=True,
                )
                session.add(fac)
                count += 1

                if count % 500 == 0:
                    session.flush()
                    log.info(f"    ... {count} diimport dari {fname}")

        session.commit()
        log.info(f"  ✓ {count} fasilitas dari {fname}, {skipped} dilewati")
        total += count

    return total


# ── 4. Import roads OSM ───────────────────────────────────────────────
def import_roads(session: Session, reset: bool = False) -> int:
    log.info("=== Import: Jaringan Jalan OSM ===")
    csv_path = RAW / "osm" / "roads.csv"
    if not csv_path.exists():
        log.warning(f"  File tidak ditemukan: {csv_path}")
        return 0

    if reset:
        deleted = session.query(Road).delete()
        session.commit()
        log.info(f"  Reset: {deleted} baris dihapus")

    existing_count = session.query(Road).count()
    if existing_count > 0 and not reset:
        log.info(f"  Skip: sudah ada {existing_count} jalan. Gunakan --reset untuk reimport.")
        return 0

    MAIN_ROAD_TYPES = {"motorway", "trunk", "primary"}
    count = 0
    skipped = 0

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            city = row.get("city", "")
            region_id = find_region_id(city, city)
            if not region_id:
                city_lower = city.lower()
                if "jakarta" in city_lower:
                    region_id = 5
                elif "bandung" in city_lower:
                    region_id = 16
                elif "bogor" in city_lower:
                    region_id = 19
                elif "bekasi" in city_lower:
                    region_id = 22
                elif "depok" in city_lower:
                    region_id = 25
                else:
                    skipped += 1
                    continue

            highway = row.get("highway_type", "tertiary")
            road = Road(
                region_id=region_id,
                road_name=(row.get("road_name") or "")[:255] or None,
                road_type=highway[:50],
                road_density=1.0,  # default, akan diupdate nanti
                length_km=safe_float(row.get("node_count"), 0) * 0.05,  # estimasi kasar
                is_main_road=highway in MAIN_ROAD_TYPES,
            )
            session.add(road)
            count += 1

            if count % 1000 == 0:
                session.flush()
                log.info(f"    ... {count} jalan diimport")

    session.commit()
    log.info(f"  ✓ {count} jalan diimport, {skipped} dilewati")
    return count


# ── Main ──────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Import data raw ke MySQL")
    parser.add_argument("--reset", action="store_true",
                        help="Hapus data lama sebelum import (kecuali regions)")
    args = parser.parse_args()

    log.info("╔══════════════════════════════════════════════╗")
    log.info("║  URIS-AI — Import Data Raw ke MySQL          ║")
    log.info("╚══════════════════════════════════════════════╝")

    engine = create_db_engine(settings.active_database_url)
    Base.metadata.create_all(bind=engine)
    session = create_session_factory(engine)()

    try:
        r1 = import_wilayah(session)
        r2 = import_weather(session, args.reset)
        r3 = import_facilities(session, args.reset)
        r4 = import_roads(session, args.reset)

        log.info("")
        log.info("══ SELESAI ══════════════════════════════════")
        log.info(f"  Wilayah     : {r1}")
        log.info(f"  Cuaca       : {r2} baris")
        log.info(f"  Fasilitas   : {r3} titik")
        log.info(f"  Jalan       : {r4} ruas")
        log.info("═════════════════════════════════════════════")

    except Exception as e:
        log.error(f"Error: {e}", exc_info=True)
        session.rollback()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
