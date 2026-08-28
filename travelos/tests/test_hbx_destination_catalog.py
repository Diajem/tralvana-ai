from __future__ import annotations

from sqlalchemy import create_engine

from travelos.live_providers.hbx_destination_catalog import (
    HbxDestination,
    InMemoryHbxDestinationCatalog,
    SqlAlchemyHbxDestinationCatalog,
)
from travelos.persistence.base import Base
from travelos.persistence.session import create_session_factory


def _destinations() -> list[HbxDestination]:
    return [
        HbxDestination(code="LON", name="London", country_code="GB"),
        HbxDestination(code="LONUS", name="London", country_code="US"),
        HbxDestination(code="SAO", name="São Paulo", country_code="BR"),
    ]


def test_in_memory_catalog_resolves_country_qualified_and_accented_names():
    catalog = InMemoryHbxDestinationCatalog(_destinations())

    assert catalog.resolve("London, United Kingdom", "GB").code == "LON"
    assert catalog.resolve("Sao Paulo").code == "SAO"
    assert catalog.resolve("London") is None


def test_catalog_treats_hbx_uk_and_iso_gb_as_equivalent():
    catalog = InMemoryHbxDestinationCatalog(
        [HbxDestination(code="LON", name="London", country_code="UK")]
    )

    assert catalog.resolve("London, United Kingdom", "GB").code == "LON"


def test_sql_catalog_treats_hbx_uk_and_iso_gb_as_equivalent():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    catalog = SqlAlchemyHbxDestinationCatalog(create_session_factory(engine))
    catalog.upsert_many([HbxDestination(code="LON", name="London", country_code="UK")])

    assert catalog.resolve("London, United Kingdom", "GB").code == "LON"
    engine.dispose()


def test_catalog_resolves_legacy_serialized_hbx_content_name():
    catalog = InMemoryHbxDestinationCatalog(
        [HbxDestination(code="LON", name="{'content': 'London'}", country_code="UK")]
    )

    assert catalog.resolve("London, United Kingdom", "GB").code == "LON"


def test_sql_catalog_resolves_legacy_serialized_hbx_content_name():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    catalog = SqlAlchemyHbxDestinationCatalog(create_session_factory(engine))
    catalog.upsert_many(
        [HbxDestination(code="LON", name="{'content': 'London'}", country_code="UK")]
    )

    assert catalog.resolve("London, United Kingdom", "GB").code == "LON"
    engine.dispose()


def test_sql_catalog_upserts_and_updates_without_duplicates():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    catalog = SqlAlchemyHbxDestinationCatalog(create_session_factory(engine))
    catalog.upsert_many(_destinations())
    catalog.upsert_many([HbxDestination(code="LON", name="London City", country_code="GB")])

    assert catalog.resolve("London", "GB") is None
    assert catalog.resolve("London City", "GB").code == "LON"
    assert catalog.resolve("Sao Paulo", "BR").code == "SAO"
    engine.dispose()
