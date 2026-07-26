import pytest

from travelos.shared.container import ServiceContainer


def test_instance_registration_and_resolution():
    container = ServiceContainer()
    service = object()

    container.register("service", service)

    assert container.resolve("service") is service
    assert container.resolve_or_none("service") is service
    assert container.has("service") is True
    assert container.registered() == ["service"]


def test_singleton_factory_is_lazy_and_called_once():
    container = ServiceContainer()
    calls = []

    def factory(current):
        calls.append(current)
        return object()

    container.singleton("service", factory)
    assert calls == []

    first = container.resolve("service")
    second = container.resolve("service")

    assert first is second
    assert calls == [container]


def test_factory_can_resolve_another_registration():
    container = ServiceContainer()
    config = {"region": "GB"}
    container.register("config", config)
    container.singleton(
        "client",
        lambda current: {"config": current.resolve("config")},
    )

    assert container.resolve("client") == {"config": config}


def test_missing_service_has_actionable_error_and_none_variant():
    container = ServiceContainer()
    container.register("known", object())

    with pytest.raises(
        KeyError,
        match=r"Service 'missing' is not registered.*known",
    ):
        container.resolve("missing")
    assert container.resolve_or_none("missing") is None


def test_child_inherits_registrations_but_owns_singleton_cache():
    parent = ServiceContainer()
    shared = object()
    parent.register("shared", shared)
    parent.singleton("scoped", lambda current: object())

    parent_scoped = parent.resolve("scoped")
    child = parent.child()

    assert child.resolve("shared") is shared
    assert child.resolve("scoped") is not parent_scoped
    assert child.resolve("scoped") is child.resolve("scoped")


def test_reset_clears_all_registration_state():
    container = ServiceContainer()
    container.register("instance", object())
    container.singleton("factory", lambda current: object())
    container.resolve("factory")

    container.reset()

    assert container.registered() == []
    assert container.has("instance") is False
    assert container.resolve_or_none("factory") is None
