from __future__ import annotations

import hashlib

import pytest

from travelos.intelligence_gateway.exceptions import ProviderConfigurationError
from travelos.intelligence_gateway.secret_reference import SecretReference
from travelos.live_providers.auth.hbx_signature_auth import HbxSignatureAuthStrategy


def test_hbx_signature_uses_api_key_secret_and_unix_timestamp(monkeypatch):
    monkeypatch.setenv("TEST_HBX_KEY", "key-123")
    monkeypatch.setenv("TEST_HBX_SECRET", "secret-456")
    auth = HbxSignatureAuthStrategy(
        api_key=SecretReference("TEST_HBX_KEY"),
        shared_secret=SecretReference("TEST_HBX_SECRET"),
        clock=lambda: 1_725_000_123.9,
    )

    headers = auth.headers()

    expected = hashlib.sha256(b"key-123secret-4561725000123").hexdigest()
    assert headers == {"Api-key": "key-123", "X-Signature": expected}
    assert "secret-456" not in repr(auth)


def test_hbx_auth_fails_closed_without_secret(monkeypatch):
    monkeypatch.setenv("TEST_HBX_KEY", "key-123")
    monkeypatch.delenv("TEST_HBX_SECRET", raising=False)
    auth = HbxSignatureAuthStrategy(
        api_key=SecretReference("TEST_HBX_KEY"),
        shared_secret=SecretReference("TEST_HBX_SECRET"),
    )

    with pytest.raises(ProviderConfigurationError) as exc_info:
        auth.headers()

    assert "TEST_HBX_SECRET" in str(exc_info.value)
    assert "key-123" not in str(exc_info.value)
