"""Fetch data jalan & fasilitas publik dari OSM per kota (bbox kecil)."""
import csv, time, sqlite3, requests
from pathlib import Path
from datetime import datetime, timezone

HEADERS  = {"User-Agent": "URIS-AI/0.1 (urban-risk-research)"}
OVERPASS = "https://overpass-api.de/api/interpreter"
OUT      = Path("data/raw/osm")
OUT.mkdir(parents=True, exist_ok=True)
TS       = datetime.now(timezone.utc).isoformat()

def log(m): print(f"[{datetime.now().strftime('%H:%M:%S')}] {m}")

def query(q, timeout=50):
    r = requests.post(OVERPASS, data={"data": q}, headers=HEADERS, timeout=timeout)
    r.raise_for_status()
    return r.json().get("elements", [])

def save(rows, csv_path, sql_path, table):
    if not rows: return
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    cols = list(rows[0].keys())
    defs = ", ".join(f'"{c}" TEXT' for c in cols)
    lines = [f'CREATE TABLE IF NOT EXISTS "{table}" ({defs});']
    for row in rows:
        vals = ", ".join(
            "NULL" if (v == "" or v is None)
            else "'" + str(v).replace("'", "''") + "'"
            for v in row.values()
        )
        lines.append(f'INSERT INTO "{table}" VALUES ({vals});')
    sql_path.write_text("\n".join(lines), encoding="utf-8")
    log(f"  → {csv_path.name} ({len(rows)} baris) + {sql_path.name}")

# Kota dengan bbox masing-masing (south,west,north,east)
CITIES = [
    ("Jakarta",  "-6.37,106.68,-6.08,106.97"),
    ("Bandung",  "-7.00,107.52,-6.83,107.72"),
    ("Bogor",    "-6.65,106.73,-6.52,106.87"),
    ("Bekasi",   "-6.32,106.93,-6.18,107.05"),
    ("Depok",    "-6.45,106.75,-6.35,106.88"),
]

# ── Jalan ────────────────────────────────────────────────────────────────────
log("=== OSM Roads ===")
road_rows = []
for city, bbox in CITIES:
    q = (f'[out:json][timeout:45];'
         f'(way["highway"~"^(motorway|trunk|primary|secondary|tertiary)$"]({bbox}););'
         f'out body qt;')
    try:
        els = query(q)
        for el in els:
            t = el.get("tags", {})
            road_rows.append({
                "osm_id": el["id"], "city": city,
                "road_name": t.get("name",""), "highway_type": t.get("highway",""),
                "oneway": t.get("oneway","no"), "lanes": t.get("lanes",""),
                "maxspeed": t.get("maxspeed",""), "surface": t.get("surface",""),
                "node_count": len(el.get("nodes",[])), "fetched_at": TS,
            })
        log(f"  ✓ {city}: {len(els)} jalan")
        time.sleep(4)
    except Exception as e:
        log(f"  ✗ {city}: {e}")
        time.sleep(5)

save(road_rows, OUT/"roads.csv", OUT/"roads.sql", "osm_roads")

# ── Fasilitas publik (sekolah, kantor pemerintah, pemadam, polisi) ────────────
log("=== OSM Fasilitas Publik ===")
pub_rows = []
for city, bbox in CITIES:
    q = (f'[out:json][timeout:45];'
         f'(node["amenity"~"^(school|university|government|townhall|fire_station|police)$"]({bbox});'
         f'way["amenity"~"^(school|university|government|townhall|fire_station|police)$"]({bbox}););'
         f'out center body qt;')
    try:
        els = query(q)
        for el in els:
            t = el.get("tags", {})
            lat = el.get("lat") or el.get("center", {}).get("lat","")
            lon = el.get("lon") or el.get("center", {}).get("lon","")
            pub_rows.append({
                "osm_id": el["id"], "osm_type": el["type"], "city": city,
                "name": t.get("name",""), "amenity": t.get("amenity",""),
                "operator": t.get("operator",""), "lat": lat, "lon": lon,
                "fetched_at": TS,
            })
        log(f"  ✓ {city}: {len(els)} fasilitas")
        time.sleep(4)
    except Exception as e:
        log(f"  ✗ {city}: {e}")
        time.sleep(5)

save(pub_rows, OUT/"fasilitas_publik.csv", OUT/"fasilitas_publik.sql", "osm_fasilitas_publik")

# ── Update SQLite DB ──────────────────────────────────────────────────────────
log("=== Update SQLite DB ===")
db = sqlite3.connect("data/raw/uris_ai_raw.db")
for sql_file in [OUT/"roads.sql", OUT/"fasilitas_publik.sql"]:
    if sql_file.exists():
        try:
            db.executescript(sql_file.read_text(encoding="utf-8"))
            log(f"  ✓ {sql_file.name}")
        except Exception as e:
            log(f"  ✗ {sql_file.name}: {e}")
db.commit(); db.close()

log("=== SELESAI ===")
for f in sorted(Path("data/raw").rglob("*")):
    if f.is_file() and f.suffix in (".csv",".sql",".db"):
        log(f"  {f.relative_to('data/raw')}  ({f.stat().st_size//1024} KB)")
