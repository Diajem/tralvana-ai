from pathlib import Path

import yaml

from app.database import session as database_session


ROOT = Path(__file__).parents[3]


def test_plain_managed_postgres_url_uses_installed_psycopg_driver(monkeypatch):
    captured = {}

    def fake_create_engine(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return object()

    monkeypatch.setattr(database_session, "create_engine", fake_create_engine)
    database_session.create_engine_from_url("postgresql://user:secret@db/tralvana")
    assert captured["url"] == "postgresql+psycopg://user:secret@db/tralvana"


def test_render_blueprint_preserves_current_site_and_uses_safe_provider_modes():
    blueprint = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
    services = {service["name"]: service for service in blueprint["services"]}

    assert services["tralvana-web"]["domains"] == ["app.tralvana.com"]
    assert services["tralvana-api"]["domains"] == ["api.tralvana.com"]
    assert all("tralvana.com" not in service["domains"] for service in services.values())

    api_environment = {
        item["key"]: item.get("value")
        for item in services["tralvana-api"]["envVars"]
        if "key" in item
    }
    assert api_environment["TRALVANA_PROVIDER_ENVIRONMENT"] == "MOCK"
    assert api_environment["TRALVANA_FLIGHT_PROVIDER_MODE"] == "MOCK"
    assert api_environment["TRALVANA_ACCOMMODATION_PROVIDER_MODE"] == "MOCK"
    assert services["tralvana-api"]["healthCheckPath"] == "/health/ready"


def test_render_database_is_paid_private_and_no_secret_is_committed():
    blueprint_text = (ROOT / "render.yaml").read_text(encoding="utf-8")
    blueprint = yaml.safe_load(blueprint_text)
    database = blueprint["databases"][0]

    assert database["plan"] == "basic-256mb"
    assert database["ipAllowList"] == []
    assert "DUFFEL_API_TOKEN" not in blueprint_text
    assert "OPENAI_API_KEY" not in blueprint_text
