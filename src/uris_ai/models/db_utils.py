"""
Database utility functions for URIS-AI system.

Provides functions for database connection, session management,
and schema initialization. Uses PyMySQL for MySQL/Azure Database for MySQL.
"""

import urllib.parse
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from .database import Base


def create_db_engine(connection_string: str, echo: bool = False) -> Engine:
    """
    Create a SQLAlchemy engine for Azure Database for MySQL.

    Accepts either:
    - MySQL URL (mysql+pymysql://user:pass@host/db)
    - Legacy ODBC string (Driver={...};Server=...;...) — converted automatically

    Args:
        connection_string: Database connection string
        echo: Whether to echo SQL statements (for debugging)

    Returns:
        SQLAlchemy Engine instance
    """
    if connection_string.startswith("mysql"):
        # MySQL URL — SSL wajib untuk Azure Database for MySQL
        # Gunakan creator function agar SSL diteruskan dengan benar ke PyMySQL
        import pymysql
        from sqlalchemy import event

        base_url = connection_string.split("?")[0]

        def _creator():
            parts = base_url.replace("mysql+pymysql://", "").split("@")
            creds, hostdb = parts[0], parts[1]
            user, password = creds.split(":", 1)
            import urllib.parse
            password = urllib.parse.unquote(password)
            host_port, db = hostdb.split("/", 1)
            host, port = (host_port.split(":") + ["3306"])[:2]
            return pymysql.connect(
                host=host,
                port=int(port),
                user=user,
                password=password,
                database=db,
                ssl={"ssl_disabled": False},
                connect_timeout=10,
            )

        engine = create_engine(
            "mysql+pymysql://",
            creator=_creator,
            echo=echo,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
    elif connection_string.startswith("sqlite"):
        engine = create_engine(connection_string, echo=echo)
    else:
        # Legacy ODBC string — convert to MySQL URL if possible,
        # otherwise fall back to mssql+pyodbc
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
