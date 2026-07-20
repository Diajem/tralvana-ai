from pathlib import Path

from sqlalchemy import text

from app.database.base import Base
from app.database.session import create_engine_from_url, create_session_factory
from app.domains.commercial.repository import SqlAlchemyCommercialRepository
from app.domains.commercial.seeding import seed_verified_affiliates


def test_health_returns_ok(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_root_returns_running(client):
    res = client.get("/")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "running"
    assert "Tralvana" in body["message"]


def test_local_frontend_origin_is_allowed(client):
    res = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3001",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert res.status_code == 200
    assert res.headers["access-control-allow-origin"] == "http://localhost:3001"


def test_readiness_fails_closed_without_database(client, monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    res = client.get("/health/ready")
    assert res.status_code == 503
    assert res.json() == {
        "status": "not_ready",
        "database_reachable": False,
        "schema_version": "unconfigured",
        "expected_schema_version": "0003",
        "affiliate_programmes": 0,
    }


def test_readiness_passes_only_after_migration_and_affiliate_seed(
    client, monkeypatch, tmp_path: Path
):
    url = f"sqlite+pysqlite:///{tmp_path / 'ready.db'}"
    engine = create_engine_from_url(url)
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    with factory.begin() as session:
        session.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
        session.execute(text("INSERT INTO alembic_version (version_num) VALUES ('0003')"))
        seed_verified_affiliates(SqlAlchemyCommercialRepository(session))
    monkeypatch.setenv("DATABASE_URL", url)

    res = client.get("/health/ready")

    assert res.status_code == 200
    assert res.json() == {
        "status": "ok",
        "database_reachable": True,
        "schema_version": "0003",
        "expected_schema_version": "0003",
        "affiliate_programmes": 11,
    }
    engine.dispose()
