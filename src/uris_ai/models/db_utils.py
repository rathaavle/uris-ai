"""
Database utility functions for URIS-AI system.

Provides functions for database connection, session management,
and schema initialization. Uses psycopg2 for PostgreSQL (Neon).
"""

import urllib.parse
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .database import Base


def create_db_engine(connection_string: str, echo: bool = False) -> Engine:
    """
    Create a SQLAlchemy engine for PostgreSQL (Neon or any PostgreSQL provider).

    Accepts either:
    - PostgreSQL URL (postgresql+psycopg2://user:pass@host/db?sslmode=require)
    - SQLite URL (sqlite:///path/to/db) for local development

    Args:
        connection_string: Database connection string
        echo: Whether to echo SQL statements (for debugging)

    Returns:
        SQLAlchemy Engine instance
    """
    if connection_string.startswith("postgresql") or connection_string.startswith("postgres"):
        # Normalize postgres:// → postgresql+psycopg2://
        url = connection_string
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgresql://") and "+psycopg2" not in url:
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)

        # Pastikan sslmode=require ada untuk Neon
        if "sslmode" not in url:
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}sslmode=require"

        engine = create_engine(
            url,
            echo=echo,
            pool_pre_ping=True,
            pool_recycle=3600,
            # Neon pakai connection pooling, set pool size kecil
            pool_size=5,
            max_overflow=2,
        )
    elif connection_string.startswith("sqlite"):
        engine = create_engine(connection_string, echo=echo)
    else:
        # Fallback untuk backward compatibility
        raise ValueError(
            f"Unsupported connection string format. "
            f"Use postgresql+psycopg2://user:pass@host/db?sslmode=require"
        )
    return engine


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    """
    Create a session factory for database sessions.

    Args:
        engine: SQLAlchemy Engine instance

    Returns:
        Session factory
    """
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session(session_factory: sessionmaker[Session]) -> Generator[Session, None, None]:
    """
    Get a database session (generator for dependency injection).

    Args:
        session_factory: Session factory from create_session_factory

    Yields:
        Database session
    """
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_database(engine: Engine) -> None:
    """
    Initialize database by creating all tables.

    Args:
        engine: SQLAlchemy Engine instance
    """
    Base.metadata.create_all(bind=engine)


def drop_all_tables(engine: Engine) -> None:
    """
    Drop all tables from the database.

    WARNING: This will delete all data!

    Args:
        engine: SQLAlchemy Engine instance
    """
    Base.metadata.drop_all(bind=engine)
