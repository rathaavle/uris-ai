"""Retry OSM data yang gagal: Depok roads + Jakarta fasilitas publik."""
import csv, time, requests
from pathlib import Path
from datetime import datetime, timezone

HEADERS  = {"User-Agent": "URIS-AI/0.1"}
OVERPASS = "https://overpass-api.de/api/interpreter"
OUT      = Path("data/raw/osm")
TS       = datetime.now(timezone.utc).isoformat()

def log(m): print(f"[{datetime.now().strftime('%H:%M:%S')}] {m}")

def osm_query(q):
    r = requests.post(OVERPASS, data={"data": q}, headers=HEADERS, timeout=55)
    r.raise_for_status()
    return r.json().get("elements", [])

# ── Depok roads ──────────────────────────────────────────────────────────────
log("Retry Depok roads (tunggu 15 detik dulu)...")
time.sleep(15)
q = ('[out:json][timeout:45];'
     '(way["highway"~"^(motorway|trunk|primary|secondary|tertiary)$"]'
     '(-6.45,106.75,-6.35,106.88););out body qt;')
try:
    els = osm_query(q)
    existing = list(csv.DictReader(open(OUT / "roads.csv", encoding="utf-8")))
    new_rows = []
    for el in els:
        t = el.get("tags", {})
        new_rows.append({
            "osm_id": el["id"], "city": "Depok",
            "road_name": t.get("name", ""), "highway_type": t.get("highway", ""),
            "oneway": t.get("oneway", "no"), "lanes": t.get("lanes", ""),
            "maxspeed": t.get("maxspeed", ""), "surface": t.get("surface", ""),
            "node_count": len(el.get("nodes", [])), "fetched_at": TS,
        })
    all_rows = existing + new_rows
    with open(OUT / "roads.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=all_rows[0].keys())
        w.writeheader(); w.writerows(all_rows)
    log(f"  OK Depok: {len(new_rows)} jalan baru, total {len(all_rows)}")
except Exception as e:
    log(f"  FAIL Depok roads: {e}")

# ── Jakarta fasilitas publik ─────────────────────────────────────────────────
log("Retry Jakarta fasilitas publik (tunggu 15 detik)...")
time.sleep(15)
q2 = ('[out:json][timeout:45];'
      '(node["amenity"~"^(school|university|government|townhall|fire_station|police)$"]'
      '(-6.37,106.68,-6.08,106.97);'
      'way["amenity"~"^(school|university|government|townhall|fire_station|police)$"]'
      '(-6.37,106.68,-6.08,106.97););out center body qt;')
try:
    els2 = osm_query(q2)
    existing2 = list(csv.DictReader(open(OUT / "fasilitas_publik.csv", encoding="utf-8")))
    new2 = []
    for el in els2:
        t = el.get("tags", {})
        lat = el.get("lat") or el.get("center", {}).get("lat", "")
        lon = el.get("lon") or el.get("center", {}).get("lon", "")
        new2.append({
            "osm_id": el["id"], "osm_type": el["type"], "city": "Jakarta",
            "name": t.get("name", ""), "amenity": t.get("amenity", ""),
            "operator": t.get("operator", ""), "lat": lat, "lon": lon,
            "fetched_at": TS,
        })
    all2 = existing2 + new2
    with open(OUT / "fasilitas_publik.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=all2[0].keys())
        w.writeheader(); w.writerows(all2)
    log(f"  OK Jakarta: {len(new2)} fasilitas baru, total {len(all2)}")
except Exception as e:
    log(f"  FAIL Jakarta fasilitas: {e}")

log("SELESAI")
for f in sorted(Path("data/raw").rglob("*")):
    if f.is_file() and f.suffix in (".csv", ".sql", ".db"):
        log(f"  {f.relative_to('data/raw')}  ({f.stat().st_size // 1024} KB)")
