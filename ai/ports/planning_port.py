"""AI-owned contract for application planning and Discovery capabilities."""

from __future__ import annotations

from typing import Any, Protocol


class PlanningPort(Protocol):
    def create_goal(
        self,
        traveller_id: str | None,
        message: str,
        entities: dict[str, str],
    ) -> dict[str, Any]: ...

    def create_trip(
        self,
        traveller_id: str | None,
        goal_id: str | None,
        entities: dict[str, str],
        profile: dict[str, Any] | None,
    ) -> dict[str, Any]: ...

    def get_goal(self, goal_id: str) -> dict[str, Any] | None: ...

    def get_trip(self, trip_id: str) -> dict[str, Any] | None: ...

    def recommend_flights(self, **kwargs: Any) -> dict[str, Any]: ...

    def recommend_accommodation(self, **kwargs: Any) -> dict[str, Any]: ...

    def recommend_destinations(self, **kwargs: Any) -> dict[str, Any]: ...

    def recommend_budget(self, **kwargs: Any) -> dict[str, Any]: ...

    def check_visa(self, **kwargs: Any) -> dict[str, Any]: ...

    def analyse_weather(self, **kwargs: Any) -> dict[str, Any]: ...

    def recommend_events(self, **kwargs: Any) -> dict[str, Any]: ...


class PlanningPortNotConfiguredError(RuntimeError):
    """The application composition root has not supplied its adapter."""


class _UnconfiguredPlanningPort:
    def __getattr__(self, _name: str):
        def unavailable(*_args: Any, **_kwargs: Any) -> Any:
            raise PlanningPortNotConfiguredError(
                "PlanningPort has not been configured by the application"
            )

        return unavailable


_planning_port: PlanningPort = _UnconfiguredPlanningPort()  # type: ignore[assignment]


def configure_planning_port(port: PlanningPort) -> None:
    """Bind the application adapter at the API composition root."""
    global _planning_port
    _planning_port = port


def get_planning_port() -> PlanningPort:
    return _planning_port
