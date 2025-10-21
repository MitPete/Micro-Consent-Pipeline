# db/session.py
# Purpose: Database session management and engine setup

"""
Database engine and session management for SQLAlchemy.
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from micro_consent_pipeline.config.settings import Settings
from db.models import Base

# Initialize settings
settings = Settings()

# Create engine with appropriate configuration
if settings.database_url.startswith('sqlite'):
    # SQLite-specific configuration
    engine = create_engine(
        settings.database_url,
        echo=settings.database_echo,
        connect_args={"check_same_thread": False},  # Allow SQLite to be used with multiple threads
        poolclass=StaticPool,  # Use static pool for SQLite
    )
else:
    # PostgreSQL and other databases
    engine = create_engine(
        settings.database_url,
        echo=settings.database_echo,
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=300,    # Recycle connections after 5 minutes
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize the database by creating all tables.

    This creates all tables defined in the models if they don't exist.
    For production, consider using Alembic migrations instead.
    """
    # Ensure the data directory exists for SQLite
    if settings.database_url.startswith('sqlite'):
        db_path = settings.database_url.replace('sqlite:///', '')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Create all tables
    Base.metadata.create_all(bind=engine)


def drop_db() -> None:
    """
    Drop all database tables.

    WARNING: This will delete all data! Use only for testing or cleanup.
    """
    Base.metadata.drop_all(bind=engine)


def get_db_sync() -> Session:
    """
    Get a synchronous database session for use outside of FastAPI.

    Returns:
        Session: SQLAlchemy database session

    Note:
        Remember to close the session when done:
        db = get_db_sync()
        try:
            # ... use db
        finally:
            db.close()
    """
    return SessionLocal()