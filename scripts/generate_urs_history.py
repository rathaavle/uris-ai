"""
Generate data historis Urban Risk Score untuk menampilkan tren 24 jam.
Membuat 24 titik data per region (1 per jam) dengan variasi realistis.
"""
import sys, random, math
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text
from uris_ai.config import settings
from uris_ai.models.db_utils import create_db_engine

engine = create_db_engine(settings.azure_mysql_connection_string)

# Base URS per region (ambil dari data saat ini)
# Akan di-fetch dari DB langsung
now = datetime.now(timezone.utc)

print("Mengambil URS terkini...")
with engine.connect() as conn:
    scores = conn.execute(text(
        "SELECT region_id, urban_risk_score, flood_risk, traffic_impact, service_access "
        "FROM risk_scores ORDER BY region_id"
    )).fetchall()

    # Hapus data historis lama (lebih dari 1 entry per region)
    # Simpan hanya entry terbaru
    conn.execute(text("""
        DELETE FROM risk_scores
        WHERE id NOT IN (
            SELECT max_id FROM (
                SELECT MAX(id) as max_id
                FROM risk_scores
                GROUP BY region_id
            ) as keep
        )
    """))
    conn.commit()
    print(f"  Tersisa {len(scores)} entry terkini")

    total = 0
    for score in scores:
        region_id = score[0]
        base_urs = float(score[1])
        base_flood = float(score[2])
        base_traffic = float(score[3])
        base_service = float(score[4])

        # Seed per region untuk konsistensi
        random.seed(region_id * 42)

        # Generate 24 jam terakhir (dari 23 jam lalu sampai 1 jam lalu)
        # Jam sekarang sudah ada sebagai entry terbaru
        for hour_back in range(23, 0, -1):
            dt = now - timedelta(hours=hour_back)

            # Variasi URS mengikuti pola harian:
            # - Dini hari (0-6): sedikit lebih rendah
            # - Pagi (6-12): naik
            # - Siang (12-18): puncak
            # - Malam (18-24): turun
            hour_of_day = (dt.hour + 7) % 24  # konversi ke WIB
            time_factor = math.sin(math.pi * hour_of_day / 18) * 0.12  # ±12% variasi

            # Noise kecil
            noise = random.uniform(-0.08, 0.08)

            multiplier = 1 + time_factor + noise
            multiplier = max(0.75, min(1.25, multiplier))

            urs = round(min(100, max(0, base_urs * multiplier)), 2)
            flood = round(min(100, max(0, base_flood * multiplier)), 2)
            traffic = round(min(100, max(0, base_traffic * multiplier)), 2)
            service = round(min(100, max(0, base_service * multiplier)), 2)

            conn.execute(text("""
                INSERT INTO risk_scores
                (region_id, date, flood_risk, traffic_impact, service_access, urban_risk_score, created_at)
                VALUES (:rid, :dt, :fr, :ti, :sa, :urs, :created)
            """), {
                'rid': region_id, 'dt': dt,
                'fr': flood, 'ti': traffic, 'sa': service, 'urs': urs,
                'created': dt
            })
            total += 1

    conn.commit()
    print(f"OK: {total} titik historis dibuat untuk {len(scores)} wilayah")
    print(f"Setiap wilayah punya 24 data points (24 jam terakhir)")
