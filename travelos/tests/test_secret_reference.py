"""
Secret references — environment-based, never logged/returned raw —
docs/SECRET_MANAGEMENT.md.
"""

from __future__ import annotations

import pytest

from travelos.intelligence_gateway.exceptions import MissingSecretError
from travelos.intelligence_gateway.secret_reference import SecretReference

_ENV_VAR = "T025_TEST_SECRET_VALUE"


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    monkeypatch.delenv(_ENV_VAR, raising=False)


class TestMissingSecretDetection:
    def test_is_present_false_when_unset(self):
        ref = SecretReference(env_var=_ENV_VAR)
        assert ref.is_present() is False

    def test_is_present_true_when_set(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "super-secret-value")
        ref = SecretReference(env_var=_ENV_VAR)
        assert ref.is_present() is True

    def test_required_and_missing_raises(self):
        ref = SecretReference(env_var=_ENV_VAR, required=True)
        with pytest.raises(MissingSecretError):
            ref.resolve()

    def test_optional_and_missing_returns_empty_string(self):
        ref = SecretReference(env_var=_ENV_VAR, required=False)
        assert ref.resolve() == ""

    def test_empty_string_env_var_counts_as_missing(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "")
        ref = SecretReference(env_var=_ENV_VAR, required=True)
        with pytest.raises(MissingSecretError):
            ref.resolve()


class TestSecretRedaction:
    def test_resolve_returns_the_actual_value(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "super-secret-value")
        ref = SecretReference(env_var=_ENV_VAR)
        assert ref.resolve() == "super-secret-value"

    def test_describe_never_includes_the_value(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "super-secret-value")
        ref = SecretReference(env_var=_ENV_VAR)
        described = ref.describe()
        assert "super-secret-value" not in str(described)
        assert described["configured"] is True

    def test_repr_never_includes_the_value(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "super-secret-value")
        ref = SecretReference(env_var=_ENV_VAR)
        assert "super-secret-value" not in repr(ref)

    def test_str_via_repr_never_includes_the_value(self, monkeypatch):
        monkeypatch.setenv(_ENV_VAR, "another-secret")
        ref = SecretReference(env_var=_ENV_VAR)
        # dataclasses without a custom __str__ fall back to __repr__
        assert "another-secret" not in str(ref)

    def test_describe_reports_configured_false_when_unset(self):
        ref = SecretReference(env_var=_ENV_VAR)
        assert ref.describe()["configured"] is False
