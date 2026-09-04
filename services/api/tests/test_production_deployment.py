from pathlib import Path

import yaml

from travelos.persistence import session as database_session


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


def test_managed_postgres_urls_are_normalized_for_migrations_and_runtime():
    assert database_session.normalize_database_url(
        "postgresql://user:secret@db/tralvana"
    ) == "postgresql+psycopg://user:secret@db/tralvana"
    assert database_session.normalize_database_url(
        "postgres://user:secret@db/tralvana"
    ) == "postgresql+psycopg://user:secret@db/tralvana"

    migration_environment = (
        ROOT / "services/api/migrations/env.py"
    ).read_text(encoding="utf-8")
    assert "return normalize_database_url(url)" in migration_environment


def test_render_blueprint_uses_dedicated_app_domain_and_safe_provider_modes():
    blueprint = yaml.safe_load((ROOT / "render.yaml").read_text(encoding="utf-8"))
    services = {service["name"]: service for service in blueprint["services"]}

    assert "domains" not in services["tralvana-api"]
    assert services["tralvana-web"]["domains"] == ["app.tralvana.com"]

    api_environment = {
        item["key"]: item.get("value")
        for item in services["tralvana-api"]["envVars"]
        if "key" in item
    }
    supplier_modes = {
        item["key"]: item
        for item in services["tralvana-api"]["envVars"]
        if item["key"] in {"TRALVANA_FLIGHT_PROVIDER_MODE", "TRALVANA_ACCOMMODATION_PROVIDER_MODE", "TRALVANA_EVENT_PROVIDER_MODE"}
    }
    assert len(supplier_modes) == 3
    assert all(item.get("sync") is False and "value" not in item for item in supplier_modes.values())
    assert api_environment["TRALVANA_PROVIDER_ENVIRONMENT"] == "MOCK"
    assert api_environment["TRALVANA_FLIGHT_MOCK_FALLBACK_ENABLED"] == "false"
    assert api_environment["TRALVANA_AUTH_MODE"] == "CLERK"
    assert api_environment["CLERK_AUTHORIZED_PARTIES"] == "https://app.tralvana.com"
    assert api_environment["CORS_ORIGINS"] == (
        "https://app.tralvana.com,https://tralvana-web.onrender.com"
    )
    assert services["tralvana-api"]["healthCheckPath"] == "/health/ready"

    web_environment = {
        item["key"]: item.get("value")
        for item in services["tralvana-web"]["envVars"]
        if "key" in item
    }
    assert web_environment["NEXT_PUBLIC_API_URL"] == "https://tralvana-api.onrender.com"
    assert web_environment["NEXT_PUBLIC_CLERK_SIGN_IN_URL"] == "/sign-in"
    assert web_environment["NEXT_PUBLIC_CLERK_SIGN_UP_URL"] == "/sign-up"

    api_secrets = {
        item["key"]: item.get("sync")
        for item in services["tralvana-api"]["envVars"]
        if item["key"] in {"CLERK_JWT_KEY", "DUFFEL_API_TOKEN"}
    }
    web_secrets = {
        item["key"]: item.get("sync")
        for item in services["tralvana-web"]["envVars"]
        if item["key"] in {"NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY", "CLERK_SECRET_KEY"}
    }
    assert api_secrets == {"CLERK_JWT_KEY": False, "DUFFEL_API_TOKEN": False}
    assert web_secrets == {
        "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY": False,
        "CLERK_SECRET_KEY": False,
    }


def test_render_production_uses_paid_instances_private_database_and_no_secret_is_committed():
    blueprint_text = (ROOT / "render.yaml").read_text(encoding="utf-8")
    blueprint = yaml.safe_load(blueprint_text)
    database = blueprint["databases"][0]

    assert database["plan"] == "basic-256mb"
    assert database["ipAllowList"] == []
    assert all(service["plan"] == "starter" for service in blueprint["services"])
    assert "duffel_test_" not in blueprint_text
    assert "duffel_live_" not in blueprint_text
    assert "OPENAI_API_KEY" not in blueprint_text
    assert "pk_test_" not in blueprint_text
    assert "pk_live_" not in blueprint_text
    assert "sk_test_" not in blueprint_text
    assert "sk_live_" not in blueprint_text


def test_browser_api_calls_use_same_origin_server_proxy():
    api_client = (ROOT / "apps/web/src/lib/api.ts").read_text(encoding="utf-8")
    proxy = (
        ROOT / "apps/web/src/app/api/[...path]/route.ts"
    ).read_text(encoding="utf-8")

    assert 'typeof window === "undefined"' in api_client
    assert ': "/api"' in api_client
    assert "process.env.TRALVANA_API_URL" in api_client

    assert "process.env.TRALVANA_API_URL" in proxy
    assert "process.env.NEXT_PUBLIC_API_URL" in proxy
    assert 'import { auth } from "@clerk/nextjs/server"' in proxy
    assert '!headers.has("authorization")' in proxy
    assert "const session = await auth()" in proxy
    assert "const token = await session.getToken()" in proxy
    assert 'headers.set("authorization", `Bearer ${token}`)' in proxy
    assert 'headers.delete(header)' in proxy
    assert 'export const POST = relay' in proxy
    assert "CLERK_SECRET_KEY" not in proxy

    assert "authTokenProvider ? await authTokenProvider()" in api_client
    assert 'headers.set("Authorization", `Bearer ${token}`)' in api_client
    assert 'credentials: init.credentials ?? "same-origin"' in api_client
    assert 'typeof payload.detail === "string"' in api_client

    middleware = (ROOT / "apps/web/src/middleware.ts").read_text(encoding="utf-8")
    assert '"/__clerk/:path*"' in middleware


def test_clerk_sso_callbacks_remain_public_until_session_is_created():
    auth_context = (
        ROOT / "apps/web/src/lib/auth-context.tsx"
    ).read_text(encoding="utf-8")
    layout = (ROOT / "apps/web/src/app/layout.tsx").read_text(encoding="utf-8")

    assert 'const PUBLIC_PATH_PREFIXES = ["/sign-in", "/sign-up"]' in auth_context
    assert "pathname.startsWith(`${prefix}/`)" in auth_context
    assert "isPublicPath(pathname)" in auth_context
    assert 'title: "Sign in to Tralvana"' in layout
    assert 'titleCombined: "Sign in to Tralvana"' in layout
    assert "Tralvava" not in layout


def test_flight_detail_uses_the_active_browser_session_instead_of_server_redirect():
    flight_detail = (
        ROOT / "apps/web/src/app/flights/[id]/page.tsx"
    ).read_text(encoding="utf-8")
    auth_context = (
        ROOT / "apps/web/src/lib/auth-context.tsx"
    ).read_text(encoding="utf-8")

    assert flight_detail.startswith('"use client";')
    assert "useTralvanaAuth" in flight_detail
    assert "await getSessionToken()" in flight_detail
    assert "getFlightOption(id, token ?? undefined)" in flight_detail
    assert "serverSessionToken" not in flight_detail
    assert "redirectToSignIn" not in flight_detail
    assert "getSessionToken: () => Promise<string | null>" in auth_context


def test_free_api_runs_migrations_and_seed_at_startup():
    startup = (ROOT / "services/api/scripts/start-production.sh").read_text(encoding="utf-8")
    dockerfile = (ROOT / "services/api/Dockerfile").read_text(encoding="utf-8")

    assert "alembic -c services/api/alembic.ini upgrade head" in startup
    assert "seed_commercial_catalogue.py" in startup
    assert "exec uvicorn" in startup
    assert 'CMD ["sh", "services/api/scripts/start-production.sh"]' in dockerfile
