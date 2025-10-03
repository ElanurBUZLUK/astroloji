"""
Database connection and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.exc import OperationalError
from .config import settings
from .models import Base

# Database URL
DATABASE_URL = settings.POSTGRES_URL

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Test connections before use
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """Create all tables"""
    Base.metadata.create_all(bind=engine)

def get_db_session() -> Session:
    """Get database session for synchronous operations"""
    return SessionLocal()
