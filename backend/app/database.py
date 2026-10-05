"""
Database configuration and session management
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Database connection string with SQLite fallback
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tender_compliance.db")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            pass
    except Exception as e:
        print(f"Warning: Primary database connection failed ({e}). Falling back to SQLite.")
        DATABASE_URL = "sqlite:///./tender_compliance.db"
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

