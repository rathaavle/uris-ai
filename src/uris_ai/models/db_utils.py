"""
Database utility functions for URIS-AI system.

Provides functions for database connection, session management,
and schema initialization.
"""

import urllib.parse
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .database import Base


def create_db_engine(connection_string: str, echo: bool = False) -> Engine:
    """
    Create a SQLAlchemy engine for Azure SQL Database.

    Accepts either:
    - ODBC connection string (Driver={...};Server=...;...)
    - SQLAlchemy URL (mssql+pyodbc://...)

    Args:
        connection_string: Database connection string
        echo: Whether to echo SQL statements (for debugging)

    Returns:
        SQLAlchemy Engine instance
    """
    # Jika sudah format SQLAlchemy URL, pakai langsung
    if connection_string.startswith("mssql") or connection_string.startswith("sqlite"):
        engine = create_engine(connection_string, echo=echo, pool_pre_ping=True)
    else:
        # Convert ODBC string ke SQLAlchemy URL
        params = urllib.parse.quote_plus(connection_string)
        url = f"mssql+pyodbc:///?odbc_connect={params}"
        engine = create_engine(url, echo=echo, pool_pre_ping=True)
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
