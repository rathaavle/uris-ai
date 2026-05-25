"""Generate risk scores awal untuk semua region."""
import sys
import urllib.parse
import random
from datetime import datetime, timezone
sys.path.insert(0, 'src')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uris_ai.config import settings
from uris_ai.models.database import Region, RiskScore

params = urllib.parse.quote_plus(settings.azure_sql_connection_string)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
Session = sessionmaker(bind=engine)
session = Session()

regions = session.query(Region).all()
print(f"Generating risk scores untuk {len(regions)} regions...")

existing = session.query(RiskScore).count()
if existing > 0:
    print(f"Sudah ada {existing} risk scores. Skip.")
    session.close()
    sys.exit(0)

random.seed(42)
now = datetime.now(timezone.utc)

scores = []
for region in regions:
    # Simulasi risk berdasarkan elevasi dan drainage capacity
    elevation = region.elevation or 10.0
    drainage = region.drainage_capacity or 150.0

    # Wilayah rendah + drainage buruk = risiko tinggi
    flood_base = max(0, min(100, (20 - elevation) * 3 + (150 - drainage) * 0.3))
    flood_risk = max(5, min(95, flood_base + random.uniform(-10, 10)))
    traffic_impact = max(5, min(95, flood_risk * 0.7 + random.uniform(-5, 15)))
    service_access = max(5, min(95, flood_risk * 0.5 + random.uniform(-10, 20)))
    urban_risk = (flood_risk * 0.5 + traffic_impact * 0.3 + service_access * 0.2)

    score = RiskScore(
        region_id=region.region_id,
        date=now,
        flood_risk=round(flood_risk, 2),
        traffic_impact=round(traffic_impact, 2),
        service_access=round(service_access, 2),
        urban_risk_score=round(urban_risk, 2),
    )
    scores.append(score)
    session.add(score)

session.commit()
session.close()

print(f"[OK] {len(scores)} risk scores berhasil dibuat")
for s in sorted(scores, key=lambda x: x.urban_risk_score, reverse=True)[:5]:
    region = next(r for r in regions if r.region_id == s.region_id)
    print(f"  {region.name}: URS={s.urban_risk_score:.1f} (flood={s.flood_risk:.1f})")
