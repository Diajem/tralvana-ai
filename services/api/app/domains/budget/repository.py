from __future__ import annotations

from app.domains.budget.models import BudgetOption


class BudgetRepository:
    """In-memory store. Replace with a PostgreSQL adapter in Sprint 3."""

    def __init__(self) -> None:
        self._store: dict[str, BudgetOption] = {}

    def save(self, option: BudgetOption) -> BudgetOption:
        self._store[option.budget_option_id] = option
        return option

    def save_many(self, options: list[BudgetOption]) -> list[BudgetOption]:
        for o in options:
            self._store[o.budget_option_id] = o
        return options

    def get(self, budget_option_id: str) -> BudgetOption | None:
        return self._store.get(budget_option_id)

    def list_by_trip(self, trip_id: str) -> list[BudgetOption]:
        return [o for o in self._store.values() if o.trip_id == trip_id]
