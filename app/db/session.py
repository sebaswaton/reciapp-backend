from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "❌ ERROR: DATABASE_URL no está configurada.\n"
        "Verifica tu docker-compose.yml o variables de entorno."
    )

print(f"✅ Conectando a: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'base de datos'}")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()