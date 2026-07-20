"""Safe database readiness inspection shared by deployment endpoints."""
from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import text

from app.database.session import create_engine_from_url, create_session_factory, database_url
from app.domains.commercial.repository import SqlAlchemyCommercialRepository

EXPECTED_SCHEMA_VERSION = "0003"
COUNT_NAMES = ("partners", "programmes", "clicks", "conversions", "commissions")


@dataclass(frozen=True, slots=True)
class DatabaseReadiness:
    configured: bool
    reachable: bool
    schema_version: str
    counts: dict[str, int]

    @property
    def ready(self) -> bool:
        return (
            self.configured
            and self.reachable
            and self.schema_version == EXPECTED_SCHEMA_VERSION
            and self.counts["programmes"] > 0
        )


def inspect_database_readiness() -> DatabaseReadiness:
    """Inspect connectivity, migration head, and catalogue seed without leaking a URL."""
    empty = {name: 0 for name in COUNT_NAMES}
    url = database_url()
    if not url:
        return DatabaseReadiness(False, False, "unconfigured", empty)

    engine = create_engine_from_url(url)
    factory = create_session_factory(engine)
    try:
        with factory() as session:
            try:
                session.execute(text("SELECT 1"))
            except Exception:
                return DatabaseReadiness(True, False, "unknown", empty)

            try:
                schema_version = session.execute(
                    text("SELECT version_num FROM alembic_version")
                ).scalar_one()
                counts = SqlAlchemyCommercialRepository(session).counts()
            except Exception:
                return DatabaseReadiness(True, True, "unknown", empty)

        return DatabaseReadiness(True, True, str(schema_version), counts)
    finally:
        engine.dispose()
