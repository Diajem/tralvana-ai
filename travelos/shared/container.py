from __future__ import annotations

from typing import Any, Callable, TypeVar

T = TypeVar("T")


class ServiceContainer:
    """
    Lightweight dependency injection container.

    Services are registered as either:
    - Instances (already-constructed objects)
    - Singleton factories (lazy-constructed, constructed once, cached)

    Usage:
        container = ServiceContainer()
        container.register("logger", my_logger)
        container.singleton("db", lambda c: Database(c.resolve("config")))

        logger = container.resolve("logger")
    """

    def __init__(self) -> None:
        self._instances: dict[str, Any] = {}
        self._factories: dict[str, Callable[[ServiceContainer], Any]] = {}
        self._singletons: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, name: str, instance: Any) -> None:
        """Register a pre-built instance."""
        self._instances[name] = instance

    def singleton(self, name: str, factory: Callable[[ServiceContainer], Any]) -> None:
        """Register a lazy singleton factory. Called once on first resolve."""
        self._factories[name] = factory

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def resolve(self, name: str) -> Any:
        """Resolve a service by name. Raises KeyError if not registered."""
        if name in self._instances:
            return self._instances[name]
        if name in self._singletons:
            return self._singletons[name]
        if name in self._factories:
            self._singletons[name] = self._factories[name](self)
            return self._singletons[name]
        raise KeyError(
            f"Service '{name}' is not registered. "
            f"Registered: {self.registered()}"
        )

    def resolve_or_none(self, name: str) -> Any | None:
        try:
            return self.resolve(name)
        except KeyError:
            return None

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def has(self, name: str) -> bool:
        return name in self._instances or name in self._factories or name in self._singletons

    def registered(self) -> list[str]:
        return sorted(set(self._instances) | set(self._factories) | set(self._singletons))

    def reset(self) -> None:
        """Clear all registrations. Primarily for use in tests."""
        self._instances.clear()
        self._factories.clear()
        self._singletons.clear()

    def child(self) -> ServiceContainer:
        """Create a child container that inherits parent registrations."""
        c = ServiceContainer()
        c._instances.update(self._instances)
        c._factories.update(self._factories)
        return c


default_container = ServiceContainer()
