from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def database_url() -> str | None:
    value = os.environ.get("DATABASE_URL", "").strip()
    return value or None


def normalize_database_url(url: str) -> str:
    """Select the installed psycopg 3 driver for managed Postgres URLs."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg://", 1)
    return url


def create_engine_from_url(url: str, *, echo: bool = False) -> Engine:
    """Create an engine; in-memory SQLite is supported for isolated tests."""
    # Managed Postgres providers commonly expose a plain ``postgresql://``
    # connection string. SQLAlchemy otherwise assumes psycopg2 for that URL,
    # while Tralvana deliberately installs psycopg 3.
    url = normalize_database_url(url)
    kwargs: dict = {"pool_pre_ping": True, "echo": echo}
    if url in {"sqlite://", "sqlite+pysqlite:///:memory:"}:
        kwargs.update(
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    return create_engine(url, **kwargs)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@contextmanager
def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
