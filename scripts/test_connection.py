"""Test koneksi Azure Database for MySQL dan inisialisasi schema."""
import sys
sys.path.insert(0, 'src')

from uris_ai.config import settings
from uris_ai.models.db_utils import create_db_engine
from uris_ai.models.database import Base
from sqlalchemy import text

print(f"Connecting to: {settings.azure_mysql_host} / {settings.azure_mysql_database}")

try:
    engine = create_db_engine(settings.azure_mysql_connection_string)

    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("KONEKSI OK")

    print("Membuat schema...")
    Base.metadata.create_all(bind=engine)
    print("SCHEMA OK")

    with engine.connect() as conn:
        result = conn.execute(text("SHOW TABLES"))
        tables = [row[0] for row in result]
    print(f"Tabel ({len(tables)}): {tables}")

except Exception as e:
    print(f"ERROR: {e}")
