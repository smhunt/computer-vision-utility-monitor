#!/usr/bin/env python3
"""
Database connection manager for PostgreSQL
"""

import os
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from .models import Base


# Database configuration from environment
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'utility_monitor')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', '***REMOVED***')

# Construct database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Global engine and session factory
_engine = None
_SessionLocal = None


def get_engine():
    """Get or create the SQLAlchemy engine"""
    global _engine

    if _engine is None:
        _engine = create_engine(
            DATABASE_URL,
            # Connection pool settings
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,   # Recycle connections after 1 hour
            echo=os.getenv('SQL_ECHO', 'false').lower() == 'true',  # Log SQL queries
        )

        # Event listener for connection establishment
        @event.listens_for(_engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Set connection parameters on connect"""
            # Set timezone
            cursor = dbapi_conn.cursor()
            cursor.execute("SET timezone='UTC'")
            cursor.close()

    return _engine


def get_session_factory():
    """Get or create the session factory"""
    global _SessionLocal

    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )

    return _SessionLocal


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions

    Usage:
        with get_db_session() as session:
            meter = session.query(Meter).filter_by(name='water_main').first()
            session.commit()
    """
    SessionLocal = get_session_factory()
    session = SessionLocal()

    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def init_database(drop_existing: bool = False):
    """
    Initialize the database schema

    Args:
        drop_existing: If True, drop all tables before creating (USE WITH CAUTION!)
    """
    engine = get_engine()

    if drop_existing:
        print("⚠️  Dropping all existing tables...")
        Base.metadata.drop_all(bind=engine)

    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")


def test_connection() -> bool:
    """
    Test database connection

    Returns:
        True if connection successful, False otherwise
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print(f"✓ Database connection successful: {DB_HOST}:{DB_PORT}/{DB_NAME}")
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False


def close_connections():
    """Close all database connections"""
    global _engine, _SessionLocal

    if _engine:
        _engine.dispose()
        _engine = None

    _SessionLocal = None
    print("✓ Database connections closed")


# Utility functions for common operations

def get_or_create(session: Session, model, defaults=None, **kwargs):
    """
    Get an existing record or create a new one

    Args:
        session: Database session
        model: SQLAlchemy model class
        defaults: Default values for creation
        **kwargs: Filter criteria

    Returns:
        Tuple of (instance, created)
    """
    instance = session.query(model).filter_by(**kwargs).first()

    if instance:
        return instance, False

    params = dict(kwargs)
    if defaults:
        params.update(defaults)

    instance = model(**params)
    session.add(instance)
    session.flush()

    return instance, True


# CLI utility for testing
if __name__ == '__main__':
    import sys
    from dotenv import load_dotenv

    load_dotenv()

    print("Database Connection Test")
    print("=" * 60)
    print(f"Host: {DB_HOST}:{DB_PORT}")
    print(f"Database: {DB_NAME}")
    print(f"User: {DB_USER}")
    print()

    # Test connection
    if test_connection():
        print()

        # Option to initialize schema
        if len(sys.argv) > 1 and sys.argv[1] == '--init':
            print("Initializing database schema...")
            init_database()
        elif len(sys.argv) > 1 and sys.argv[1] == '--reset':
            print("⚠️  RESETTING DATABASE (dropping all tables)...")
            response = input("Are you sure? Type 'yes' to confirm: ")
            if response.lower() == 'yes':
                init_database(drop_existing=True)
            else:
                print("Cancelled.")
        else:
            print("Options:")
            print("  python -m src.database.connection --init    # Initialize schema")
            print("  python -m src.database.connection --reset   # Reset database (drops all tables)")
    else:
        print()
        print("Connection failed. Check your environment variables:")
        print("  POSTGRES_HOST")
        print("  POSTGRES_PORT")
        print("  POSTGRES_DB")
        print("  POSTGRES_USER")
        print("  POSTGRES_PASSWORD")
