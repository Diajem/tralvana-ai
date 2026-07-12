"""
API-key, bearer-token, and OAuth2 client-credentials authentication
strategies — configuration, secret absence, and secret redaction
(docs/PROVIDER_AUTHENTICATION.md). Every secret is loaded through the
existing SecretReference (T-025) — no live authentication call is made
anywhere in this file.
"""

from __future__ import annotations

import pytest

from travelos.intelligence_gateway.exceptions import ProviderConfigurationError
from travelos.intelligence_gateway.secret_reference import SecretReference
from travelos.live_providers.auth.api_key_auth import ApiKeyAuthStrategy
from travelos.live_providers.auth.bearer_token_auth import BearerTokenAuthStrategy
from travelos.live_providers.auth.oauth2_client_credentials_auth import (
    OAuth2ClientCredentialsAuthStrategy,
)

_KEY_VAR = "T026_TEST_API_KEY"
_CLIENT_ID_VAR = "T026_TEST_CLIENT_ID"
_CLIENT_SECRET_VAR = "T026_TEST_CLIENT_SECRET"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for var in (_KEY_VAR, _CLIENT_ID_VAR, _CLIENT_SECRET_VAR):
        monkeypatch.delenv(var, raising=False)


class TestApiKeyAuthentication:
    def test_not_configured_when_env_var_unset(self):
        strategy = ApiKeyAuthStrategy(secret=SecretReference(env_var=_KEY_VAR))
        assert strategy.is_configured() is False

    def test_configured_when_env_var_set(self, monkeypatch):
        monkeypatch.setenv(_KEY_VAR, "some-key")
        strategy = ApiKeyAuthStrategy(secret=SecretReference(env_var=_KEY_VAR))
        assert strategy.is_configured() is True

    def test_headers_raises_when_unconfigured(self):
        strategy = ApiKeyAuthStrategy(secret=SecretReference(env_var=_KEY_VAR))
        with pytest.raises(ProviderConfigurationError):
            strategy.headers()

    def test_headers_uses_configured_header_name(self, monkeypatch):
        monkeypatch.setenv(_KEY_VAR, "abc123")
        strategy = ApiKeyAuthStrategy(secret=SecretReference(env_var=_KEY_VAR), header_name="X-Custom-Key")
        assert strategy.headers() == {"X-Custom-Key": "abc123"}

    def test_headers_default_header_name(self, monkeypatch):
        monkeypatch.setenv(_KEY_VAR, "abc123")
        strategy = ApiKeyAuthStrategy(secret=SecretReference(env_var=_KEY_VAR))
        assert strategy.headers() == {"X-API-Key": "abc123"}


class TestBearerTokenAuthentication:
    def test_not_configured_when_env_var_unset(self):
        strategy = BearerTokenAuthStrategy(secret=SecretReference(env_var=_KEY_VAR))
        assert strategy.is_configured() is False

    def test_headers_raises_when_unconfigured(self):
        strategy = BearerTokenAuthStrategy(secret=SecretReference(env_var=_KEY_VAR))
        with pytest.raises(ProviderConfigurationError):
            strategy.headers()

    def test_headers_bearer_prefix(self, monkeypatch):
        monkeypatch.setenv(_KEY_VAR, "my-token")
        strategy = BearerTokenAuthStrategy(secret=SecretReference(env_var=_KEY_VAR))
        assert strategy.headers() == {"Authorization": "Bearer my-token"}


class TestOAuth2ClientCredentialsConfiguration:
    def test_not_configured_when_neither_secret_set(self):
        strategy = OAuth2ClientCredentialsAuthStrategy(
            client_id=SecretReference(env_var=_CLIENT_ID_VAR),
            client_secret=SecretReference(env_var=_CLIENT_SECRET_VAR),
            token_url="https://example-provider.invalid/oauth/token",
        )
        assert strategy.is_configured() is False

    def test_not_configured_when_only_client_id_set(self, monkeypatch):
        monkeypatch.setenv(_CLIENT_ID_VAR, "id-only")
        strategy = OAuth2ClientCredentialsAuthStrategy(
            client_id=SecretReference(env_var=_CLIENT_ID_VAR),
            client_secret=SecretReference(env_var=_CLIENT_SECRET_VAR),
            token_url="https://example-provider.invalid/oauth/token",
        )
        assert strategy.is_configured() is False

    def test_configured_when_both_secrets_set(self, monkeypatch):
        monkeypatch.setenv(_CLIENT_ID_VAR, "id")
        monkeypatch.setenv(_CLIENT_SECRET_VAR, "secret")
        strategy = OAuth2ClientCredentialsAuthStrategy(
            client_id=SecretReference(env_var=_CLIENT_ID_VAR),
            client_secret=SecretReference(env_var=_CLIENT_SECRET_VAR),
            token_url="https://example-provider.invalid/oauth/token",
        )
        assert strategy.is_configured() is True

    def test_headers_raises_when_secrets_unset(self):
        strategy = OAuth2ClientCredentialsAuthStrategy(
            client_id=SecretReference(env_var=_CLIENT_ID_VAR),
            client_secret=SecretReference(env_var=_CLIENT_SECRET_VAR),
            token_url="https://example-provider.invalid/oauth/token",
        )
        with pytest.raises(ProviderConfigurationError):
            strategy.headers()

    def test_headers_raises_when_configured_but_no_token_fetched(self, monkeypatch):
        # Configured secrets alone aren't enough — no live token exchange
        # is implemented (T-026, interface only).
        monkeypatch.setenv(_CLIENT_ID_VAR, "id")
        monkeypatch.setenv(_CLIENT_SECRET_VAR, "secret")
        strategy = OAuth2ClientCredentialsAuthStrategy(
            client_id=SecretReference(env_var=_CLIENT_ID_VAR),
            client_secret=SecretReference(env_var=_CLIENT_SECRET_VAR),
            token_url="https://example-provider.invalid/oauth/token",
        )
        with pytest.raises(ProviderConfigurationError):
            strategy.headers()

    def test_headers_succeed_once_a_token_is_simulated(self, monkeypatch):
        monkeypatch.setenv(_CLIENT_ID_VAR, "id")
        monkeypatch.setenv(_CLIENT_SECRET_VAR, "secret")
        strategy = OAuth2ClientCredentialsAuthStrategy(
            client_id=SecretReference(env_var=_CLIENT_ID_VAR),
            client_secret=SecretReference(env_var=_CLIENT_SECRET_VAR),
            token_url="https://example-provider.invalid/oauth/token",
        )
        strategy.set_cached_token("simulated-token")
        assert strategy.headers() == {"Authorization": "Bearer simulated-token"}


class TestSecretRedactionAcrossStrategies:
    def test_api_key_never_appears_in_strategy_repr(self, monkeypatch):
        monkeypatch.setenv(_KEY_VAR, "should-not-leak")
        strategy = ApiKeyAuthStrategy(secret=SecretReference(env_var=_KEY_VAR))
        assert "should-not-leak" not in repr(strategy)

    def test_bearer_token_never_appears_in_strategy_repr(self, monkeypatch):
        monkeypatch.setenv(_KEY_VAR, "should-not-leak")
        strategy = BearerTokenAuthStrategy(secret=SecretReference(env_var=_KEY_VAR))
        assert "should-not-leak" not in repr(strategy)

    def test_oauth2_cached_token_never_appears_in_strategy_repr(self, monkeypatch):
        monkeypatch.setenv(_CLIENT_ID_VAR, "id")
        monkeypatch.setenv(_CLIENT_SECRET_VAR, "secret-value")
        strategy = OAuth2ClientCredentialsAuthStrategy(
            client_id=SecretReference(env_var=_CLIENT_ID_VAR),
            client_secret=SecretReference(env_var=_CLIENT_SECRET_VAR),
            token_url="https://example-provider.invalid/oauth/token",
        )
        strategy.set_cached_token("leaked-if-shown")
        assert "leaked-if-shown" not in repr(strategy)
        assert "secret-value" not in repr(strategy)
