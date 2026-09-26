from __future__ import annotations

import base64

import pytest

from travelos.intelligence_gateway.exceptions import ProviderConfigurationError
from travelos.intelligence_gateway.secret_reference import SecretReference
from travelos.live_providers.auth.basic_auth import BasicAuthStrategy


def _auth() -> BasicAuthStrategy:
    return BasicAuthStrategy(SecretReference("TEST_BASIC_USER"), SecretReference("TEST_BASIC_PASSWORD"))


def test_basic_auth_is_not_configured_without_both_values(monkeypatch):
    monkeypatch.setenv("TEST_BASIC_USER", "partner")
    monkeypatch.delenv("TEST_BASIC_PASSWORD", raising=False)
    assert not _auth().is_configured()
    with pytest.raises(ProviderConfigurationError):
        _auth().headers()


def test_basic_auth_builds_standard_header_without_exposing_secrets(monkeypatch):
    monkeypatch.setenv("TEST_BASIC_USER", "partner")
    monkeypatch.setenv("TEST_BASIC_PASSWORD", "sandbox-secret")
    expected = base64.b64encode(b"partner:sandbox-secret").decode("ascii")
    assert _auth().headers() == {"Authorization": f"Basic {expected}"}
