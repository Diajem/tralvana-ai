"""T-031 Clerk authentication and traveller-ownership acceptance tests."""

from __future__ import annotations

import time

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from app.auth.config import AuthConfigurationError, AuthMode, AuthSettings
from app.auth.dependencies import reset_authenticator


@pytest.fixture
def clerk_auth(monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    monkeypatch.setenv("TRALVANA_AUTH_MODE", "CLERK")
    monkeypatch.setenv("CLERK_JWT_KEY", public_pem)
    monkeypatch.setenv("CLERK_AUTHORIZED_PARTIES", "http://localhost:3001")
    reset_authenticator()

    def token(user_id: str, *, authorized_party: str = "http://localhost:3001") -> str:
        now = int(time.time())
        return jwt.encode(
            {
                "sub": user_id,
                "sid": f"sess_{user_id}",
                "azp": authorized_party,
                "iat": now,
                "nbf": now,
                "exp": now + 300,
            },
            private_key,
            algorithm="RS256",
        )

    yield token
    reset_authenticator()


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_health_and_demo_remain_public_when_clerk_is_enabled(client, clerk_auth):
    assert client.get("/health").status_code == 200
    assert client.post("/demo/japan-football-food").status_code == 200


def test_protected_api_rejects_missing_session(client, clerk_auth):
    response = client.get("/traveller/profile/user_missing")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


def test_verified_clerk_subject_becomes_traveller_id(
    client, sample_profile, clerk_auth
):
    response = client.post(
        "/traveller/profile",
        json=sample_profile,
        headers=_headers(clerk_auth("user_clerk_123")),
    )
    assert response.status_code == 201
    assert response.json()["id"] == "user_clerk_123"


def test_cross_account_profile_access_is_forbidden(
    client, sample_profile, clerk_auth
):
    owner_headers = _headers(clerk_auth("user_owner"))
    intruder_headers = _headers(clerk_auth("user_intruder"))
    assert client.post(
        "/traveller/profile", json=sample_profile, headers=owner_headers
    ).status_code == 201

    response = client.get(
        "/traveller/profile/user_owner",
        headers=intruder_headers,
    )
    assert response.status_code == 403


def test_goal_creation_ignores_client_supplied_identity(client, clerk_auth):
    response = client.post(
        "/goals",
        json={"traveller_id": "user_other", "title": "Not mine"},
        headers=_headers(clerk_auth("user_owner")),
    )
    assert response.status_code == 201
    assert response.json()["traveller_id"] == "user_owner"


def test_discovery_results_are_bound_to_and_readable_only_by_owner(
    client, clerk_auth
):
    owner_headers = _headers(clerk_auth("user_discovery_owner"))
    response = client.post(
        "/destinations/recommend",
        json={"traveller_id": "untrusted-client-id", "city": "Tokyo"},
        headers=owner_headers,
    )
    assert response.status_code == 201
    assert response.json()["traveller_id"] == "user_discovery_owner"
    option_id = response.json()["destination_options"][0]["destination_option_id"]

    intruder = client.get(
        f"/destinations/{option_id}",
        headers=_headers(clerk_auth("user_discovery_intruder")),
    )
    assert intruder.status_code == 403


def test_conversation_cannot_be_resumed_by_another_account(client, clerk_auth):
    owner = client.post(
        "/conversation/message",
        json={"message": "I need travel advice"},
        headers=_headers(clerk_auth("user_conversation_owner")),
    )
    assert owner.status_code == 200

    intruder = client.post(
        "/conversation/message",
        json={
            "message": "Continue that plan",
            "conversation_id": owner.json()["conversation_id"],
        },
        headers=_headers(clerk_auth("user_conversation_intruder")),
    )
    assert intruder.status_code == 403


def test_invalid_authorized_party_is_rejected(client, clerk_auth):
    response = client.get(
        "/traveller/profile/user_owner",
        headers=_headers(clerk_auth("user_owner", authorized_party="https://evil.example")),
    )
    assert response.status_code == 401


def test_development_auth_is_disabled_by_default(monkeypatch):
    monkeypatch.delenv("TRALVANA_AUTH_MODE", raising=False)
    monkeypatch.delenv("CLERK_JWT_KEY", raising=False)
    monkeypatch.delenv("CLERK_AUTHORIZED_PARTIES", raising=False)
    monkeypatch.setenv("TRAVELOS_ENV", "development")
    assert AuthSettings.from_environment().mode is AuthMode.DISABLED


def test_production_cannot_disable_authentication(monkeypatch):
    monkeypatch.setenv("TRAVELOS_ENV", "production")
    monkeypatch.setenv("TRALVANA_AUTH_MODE", "DISABLED")
    with pytest.raises(AuthConfigurationError, match="Production requires"):
        AuthSettings.from_environment()


def test_clerk_mode_requires_networkless_verification_material(monkeypatch):
    monkeypatch.setenv("TRALVANA_AUTH_MODE", "CLERK")
    monkeypatch.delenv("CLERK_JWT_KEY", raising=False)
    monkeypatch.delenv("CLERK_AUTHORIZED_PARTIES", raising=False)
    with pytest.raises(
        AuthConfigurationError,
        match="CLERK_JWT_KEY, CLERK_AUTHORIZED_PARTIES",
    ):
        AuthSettings.from_environment()
