"""Test koneksi Azure SQL dan inisialisasi schema."""
import sys
import urllib.parse
sys.path.insert(0, 'src')

from uris_ai.config import settings
from uris_ai.models.database import Base
from sqlalchemy import create_engine, text

print(f"Connecting to: {settings.azure_sql_server} / {settings.azure_sql_database}")

# Build SQLAlchemy URL dari komponen individual (bukan ODBC string)
params = urllib.parse.quote_plus(
    f"Driver={{ODBC Driver 18 for SQL Server}};"
    f"Server=tcp:{settings.azure_sql_server}.database.windows.net,1433;"
    f"Database={settings.azure_sql_database};"
    f"Uid={settings.azure_sql_username};"
    f"Pwd={settings.azure_sql_password};"
    f"Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
)
db_url = f"mssql+pyodbc:///?odbc_connect={params}"

try:
    engine = create_engine(db_url, echo=False, pool_pre_ping=True)

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("KONEKSI OK")

    print("Membuat schema...")
    Base.metadata.create_all(bind=engine)
    print("SCHEMA OK")

    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE'"
        ))
        tables = [row[0] for row in result]
    print(f"Tabel dibuat ({len(tables)}): {tables}")

except Exception as e:
    print(f"ERROR: {e}")
