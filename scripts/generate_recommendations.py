"""Generate rekomendasi otomatis berdasarkan risk score tiap wilayah."""
import sys
import urllib.parse
from datetime import datetime, timezone, timedelta
sys.path.insert(0, 'src')

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from uris_ai.config import settings
from uris_ai.models.database import Region, RiskScore, Recommendation

params = urllib.parse.quote_plus(settings.azure_sql_connection_string)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")
Session = sessionmaker(bind=engine)
session = Session()

# Ambil risk score terbaru per region
subq = (
    session.query(RiskScore.region_id, func.max(RiskScore.date).label("max_date"))
    .group_by(RiskScore.region_id)
    .subquery()
)
latest_scores = (
    session.query(RiskScore)
    .join(subq, (RiskScore.region_id == subq.c.region_id) & (RiskScore.date == subq.c.max_date))
    .all()
)

regions = {r.region_id: r.name for r in session.query(Region).all()}
now = datetime.now(timezone.utc)
count = 0

# Template rekomendasi berdasarkan kategori risiko
RECOMMENDATIONS = {
    "KRITIS": [
        ("alert",   "EVAKUASI SEGERA: Wilayah ini dalam kondisi darurat banjir. Segera evakuasi ke tempat yang lebih tinggi.", "Segera"),
        ("alert",   "Hindari semua perjalanan ke wilayah ini. Jalan utama terendam banjir.", "Segera"),
        ("service", "Posko darurat banjir telah dibuka. Hubungi 119 untuk bantuan evakuasi.", "Segera"),
    ],
    "TINGGI": [
        ("alert",   "WASPADA BANJIR: Risiko banjir tinggi di wilayah ini. Siapkan tas darurat dan pantau informasi terkini.", "Waspada"),
        ("route",   "Gunakan rute alternatif. Hindari jalan-jalan di dekat sungai dan daerah rendah.", "Waspada"),
        ("service", "Fasilitas kesehatan di wilayah ini mungkin terdampak. Siapkan obat-obatan darurat.", "Waspada"),
    ],
    "SEDANG": [
        ("alert",   "Pantau kondisi cuaca dan tinggi muka air secara berkala.", "Siaga"),
        ("route",   "Beberapa ruas jalan mungkin tergenang. Periksa kondisi jalan sebelum bepergian.", "Siaga"),
    ],
    "RENDAH": [
        ("alert",   "Kondisi wilayah relatif aman. Tetap waspada terhadap perubahan cuaca.", "Siaga"),
    ],
}

def get_category(score):
    if score >= 75: return "KRITIS"
    if score >= 50: return "TINGGI"
    if score >= 25: return "SEDANG"
    return "RENDAH"

for score in latest_scores:
    category = get_category(score.urban_risk_score)
    templates = RECOMMENDATIONS.get(category, [])
    expires = now + timedelta(hours=24)

    for rec_type, description, urgency in templates:
        rec = Recommendation(
            region_id=score.region_id,
            recommendation_type=rec_type,
            description=description,
            urgency_level=urgency,
            created_at=now,
            expires_at=expires,
            is_active=True,
        )
        session.add(rec)
        count += 1

session.commit()
session.close()

print(f"[OK] {count} rekomendasi dibuat untuk {len(latest_scores)} wilayah")
print("\nContoh per kategori:")
for cat in ["KRITIS", "TINGGI", "SEDANG", "RENDAH"]:
    matching = [s for s in latest_scores if get_category(s.urban_risk_score) == cat]
    if matching:
        names = [regions.get(s.region_id, "?") for s in matching[:3]]
        print(f"  {cat} ({len(matching)} wilayah): {', '.join(names)}")
