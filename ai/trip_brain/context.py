"""
Context Builder — assembles Traveller + Goal + Trip Context once per Trip
Brain pass, so the selected Discovery modules it calls don't each
independently re-fetch the same data.

Request-scoped only: built at the start of one TripBrain.plan() call and
discarded afterward. Not a new persistent store — reads Goal/Trip state
through the AI-owned PlanningPort.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ai.ports import PlanningPort, get_planning_port

@dataclass
class TripBrainContext:
    traveller_id: str | None
    trip_id: str | None
    goal_id: str | None
    entities: dict[str, str] = field(default_factory=dict)
    profile: dict[str, Any] | None = None
    goal: dict[str, Any] | None = None
    trip: dict[str, Any] | None = None

    @property
    def destination(self) -> str:
        entity_destination = self.entities.get("destination", "")
        if entity_destination:
            return entity_destination
        trip_destination = (self.trip or {}).get("destination", "")
        if trip_destination and trip_destination != "TBD":
            return trip_destination
        return ""

    @property
    def has_dates(self) -> bool:
        if self.entities.get("date_hint") or self.entities.get("month"):
            return True
        return bool((self.trip or {}).get("duration_days"))

    @property
    def has_exact_dates(self) -> bool:
        if self.entities.get("start_date") and self.entities.get("end_date"):
            return True
        timeframe = (self.goal or {}).get("timeframe", {})
        return bool(timeframe.get("earliest") and timeframe.get("latest"))

    @property
    def declared_budget(self) -> dict[str, Any] | None:
        amount = self.entities.get("budget_amount")
        currency = self.entities.get("budget_currency")
        if amount:
            return {"amount": float(amount), "currency": currency or "USD"}
        budget = (self.goal or {}).get("budget", {})
        if budget.get("amount") is not None:
            return {
                "amount": budget["amount"],
                "currency": budget.get("currency", "USD"),
            }
        return None

    @property
    def nationality(self) -> str | None:
        if self.entities.get("nationality"):
            return self.entities["nationality"]
        if self.profile:
            return self.profile.get("identity", {}).get("nationality")
        return None

    @property
    def nationality_check_needed(self) -> bool:
        """Visa Intelligence is relevant when nationality differs from the
        destination or is unknown — docs/TRIP_BRAIN_ARCHITECTURE.md's
        Decision Lifecycle table."""
        if not self.destination:
            return False
        nationality = self.nationality
        if not nationality:
            return True
        return nationality.strip().lower() != self.destination.strip().lower()

    @property
    def goal_has_budget_cap(self) -> bool:
        if not self.goal:
            return False
        budget = self.goal.get("budget", {})
        return (
            budget.get("max_usd") is not None
            or budget.get("amount") is not None
        )

    @property
    def party_size_known(self) -> bool:
        travellers = (self.goal or {}).get("travellers") or (self.trip or {}).get("travellers")
        if not travellers:
            return False
        return bool(travellers.get("adults"))

    @property
    def interests(self) -> list[str]:
        entity_interests = [
            value for value in self.entities.get("interests", "").split(",")
            if value
        ]
        if entity_interests:
            return entity_interests
        return list((self.goal or {}).get("interests", []))

    @property
    def has_event_interest(self) -> bool:
        event_terms = {
            "event", "events", "fashion", "style", "design", "soccer",
            "football", "sport", "match", "music", "concert", "festival",
            "theatre", "theater",
        }
        return any(
            any(term in interest.lower() for term in event_terms)
            for interest in self.interests
        )


class ContextBuilder:
    """Reads the two Knowledge Sources every Discovery module's Scorer
    already reads (ai/memory Traveller Context, Goals/Trips domain) — no
    new memory store, per docs/TRIP_BRAIN_ARCHITECTURE.md's Memory Usage
    section."""

    def __init__(self, planning_port: PlanningPort | None = None) -> None:
        self._planning_port = planning_port

    def build(
        self,
        traveller_id: str | None,
        trip_id: str | None,
        goal_id: str | None,
        entities: dict[str, str],
        profile: dict[str, Any] | None,
    ) -> TripBrainContext:
        goal: dict[str, Any] | None = None
        if goal_id:
            try:
                goal = self._port.get_goal(goal_id)
            except Exception:
                goal = None

        trip: dict[str, Any] | None = None
        if trip_id:
            try:
                trip = self._port.get_trip(trip_id)
            except Exception:
                trip = None

        return TripBrainContext(
            traveller_id=traveller_id,
            trip_id=trip_id,
            goal_id=goal_id,
            entities=entities,
            profile=profile,
            goal=goal,
            trip=trip,
        )

    @property
    def _port(self) -> PlanningPort:
        return self._planning_port or get_planning_port()
