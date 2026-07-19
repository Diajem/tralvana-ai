from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_commercial_migration_upgrades_and_downgrades(tmp_path: Path, monkeypatch):
    database_path = tmp_path / "migration.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+pysqlite:///{database_path}")
    config = Config("services/api/alembic.ini")

    command.upgrade(config, "head")
    engine = create_engine(f"sqlite+pysqlite:///{database_path}")
    assert {
        "commercial_partners", "affiliate_programmes", "outbound_clicks",
        "affiliate_conversions", "commission_records", "alembic_version",
    } <= set(inspect(engine).get_table_names())

    command.downgrade(config, "base")
    assert set(inspect(engine).get_table_names()) == {"alembic_version"}
    engine.dispose()
