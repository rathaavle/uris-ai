"""Buat user admin untuk testing API."""
import sys
sys.path.insert(0, 'src')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uris_ai.config import settings
from uris_ai.models.database import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from uris_ai.models.db_utils import create_db_engine

engine = create_db_engine(settings.azure_mysql_connection_string)
Session = sessionmaker(bind=engine)
session = Session()

users_to_create = [
    {"username": "admin",  "email": "admin@urisai.com",  "password": "Admin123!", "role": "government"},
    {"username": "public", "email": "public@urisai.com", "password": "Admin123!", "role": "public"},
]

for u in users_to_create:
    existing = session.query(User).filter(User.username == u["username"]).first()
    if existing:
        print(f"[SKIP] User '{u['username']}' sudah ada")
        continue
    user = User(
        username=u["username"],
        email=u["email"],
        password_hash=pwd_context.hash(u["password"]),
        role=u["role"],
        is_active=True,
    )
    session.add(user)
    print(f"[OK] User '{u['username']}' (role: {u['role']}) dibuat")

session.commit()
session.close()
print("\nSemua user siap. Password: Admin123!")
print("Roles: government | public")

