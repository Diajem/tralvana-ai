"""Seed verified Tralvana affiliates. Run after `alembic upgrade head`."""
from __future__ import annotations

from app.database.session import create_engine_from_url, create_session_factory, database_url
from app.domains.commercial.repository import SqlAlchemyCommercialRepository
from app.domains.commercial.seeding import seed_verified_affiliates


def main() -> None:
    url = database_url()
    if not url:
        raise SystemExit("DATABASE_URL is required")
    engine = create_engine_from_url(url)
    factory = create_session_factory(engine)
    try:
        with factory.begin() as session:
            created = seed_verified_affiliates(SqlAlchemyCommercialRepository(session))
        print(
            f"Verified affiliate catalogue ready: {created['partners']} partners and "
            f"{created['programmes']} programmes added."
        )
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
