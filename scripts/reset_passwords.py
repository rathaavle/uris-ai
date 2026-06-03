"""Reset password semua user pakai sha256_crypt (kompatibel dengan auth_service)."""
import sys
sys.path.insert(0, 'src')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uris_ai.config import settings
from uris_ai.models.database import User
from uris_ai.services.auth_service import AuthService

auth = AuthService(secret_key=settings.secret_key)

from uris_ai.models.db_utils import create_db_engine

engine = create_db_engine(settings.azure_mysql_connection_string)
Session = sessionmaker(bind=engine)
session = Session()

users = [
    ("admin",     "Admin123!"),
    ("responder", "Admin123!"),
    ("public",    "Admin123!"),
]

for username, password in users:
    user = session.query(User).filter(User.username == username).first()
    if user:
        user.password_hash = auth.hash_password(password)
        print(f"[OK] Password '{username}' di-reset")
    else:
        print(f"[SKIP] User '{username}' tidak ditemukan")

session.commit()
session.close()
print("\nSelesai. Login dengan password: Admin123!")

