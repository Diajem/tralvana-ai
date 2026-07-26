import importlib
from types import SimpleNamespace

import pytest

from travelos.registry.service_registry import ServiceRegistry

service_registry_module = importlib.import_module(
    "travelos.registry.service_registry"
)


def test_registry_lists_known_services_in_stable_order():
    registry = ServiceRegistry()

    assert registry.available() == sorted(registry.available())
    assert {
        "traveller_service",
        "goal_service",
        "conversation_engine",
        "knowledge_service",
        "trip_planning_service",
        "memory_service",
    } == set(registry.available())


def test_manual_registration_supports_override_and_extension():
    registry = ServiceRegistry()
    service = object()

    registry.register("custom_service", service)

    assert registry.get("custom_service") is service
    assert registry.is_known("custom_service") is True
    assert registry.loaded() == ["custom_service"]


def test_unknown_service_error_names_available_services():
    registry = ServiceRegistry()

    with pytest.raises(KeyError, match="Unknown service: 'missing'"):
        registry.get("missing")


def test_lazy_resolution_is_cached(monkeypatch):
    registry = ServiceRegistry()
    service = object()
    calls = []

    def fake_import(module_path):
        calls.append(module_path)
        return SimpleNamespace(goal_service=service)

    monkeypatch.setattr(service_registry_module.importlib, "import_module", fake_import)

    assert registry.get("goal_service") is service
    assert registry.get("goal_service") is service
    assert calls == ["app.domains.goals.service"]


def test_import_failure_becomes_actionable_runtime_error(monkeypatch):
    registry = ServiceRegistry()

    def fail_import(module_path):
        raise ImportError("dependency missing")

    monkeypatch.setattr(service_registry_module.importlib, "import_module", fail_import)

    with pytest.raises(
        RuntimeError,
        match="Cannot import service 'goal_service'.*dependency missing",
    ):
        registry.get("goal_service")


def test_missing_service_attribute_becomes_actionable_runtime_error(monkeypatch):
    registry = ServiceRegistry()
    monkeypatch.setattr(
        service_registry_module.importlib,
        "import_module",
        lambda module_path: SimpleNamespace(),
    )

    with pytest.raises(
        RuntimeError,
        match="has no attribute 'goal_service'",
    ):
        registry.get("goal_service")


def test_reset_clears_resolved_cache():
    registry = ServiceRegistry()
    registry.register("custom", object())

    registry.reset()

    assert registry.loaded() == []
    assert registry.is_known("custom") is False
