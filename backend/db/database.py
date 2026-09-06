# backend/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
import os
from dotenv import load_dotenv

# Build an absolute path to backend/.env regardless of where this script is run from
env_path = os.path.join(os.path.dirname(__file__), "../.env")
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")

# NullPool: Supabase's Session Pooler (Supavisor) already manages pooling on
# its side. Letting SQLAlchemy also hold its own connection pool on top of
# that leads to stale/dropped connections. NullPool makes SQLAlchemy open a
# fresh connection per request and close it right after, instead.
engine = create_engine(DATABASE_URL, poolclass=NullPool)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()