from __future__ import annotations

from typing import Any

from app.domains.goals.models import Goal


class GoalRepository:
    """In-memory store. Replace with a PostgreSQL adapter in Sprint 3."""

    def __init__(self) -> None:
        self._store: dict[str, Goal] = {}

    def save(self, goal: Goal) -> Goal:
        self._store[goal.goal_id] = goal
        return goal

    def get(self, goal_id: str) -> Goal | None:
        return self._store.get(goal_id)

    def list_by_traveller(self, traveller_id: str) -> list[Goal]:
        return [g for g in self._store.values() if g.traveller_id == traveller_id]

    def update(self, goal_id: str, updates: dict[str, Any]) -> Goal | None:
        goal = self._store.get(goal_id)
        if not goal:
            return None
        for key, value in updates.items():
            if hasattr(goal, key) and value is not None:
                setattr(goal, key, value)
        return goal

    def delete(self, goal_id: str) -> bool:
        if goal_id in self._store:
            del self._store[goal_id]
            return True
        return False
