"""
Database configuration and connection management
"""
import os
from databases import Database
from sqlalchemy import create_engine, MetaData
from sqlalchemy.pool import StaticPool
from .models import Base

# Database URL - using SQLite for simplicity
DATABASE_URL = "sqlite:///./data/app.db"

# Ensure data directory exists
os.makedirs("./data", exist_ok=True)

# Database instance for async operations
database = Database(
    DATABASE_URL,
    force_rollback=False,
    min_size=1,
    max_size=5
)

# SQLAlchemy engine for sync operations (migrations, etc.)
engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
        "timeout": 30
    },
    poolclass=StaticPool,
    echo=False
)

metadata = MetaData()


def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)


def get_database() -> Database:
    """Get database instance"""
    return database


async def connect_database():
    """Connect to database"""
    await database.connect()


async def disconnect_database():
    """Disconnect from database"""
    await database.disconnect()