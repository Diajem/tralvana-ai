from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.database.session import (
    create_engine_from_url,
    create_session_factory,
    database_url,
)
from app.domains.goals.models import Goal
from app.domains.goals.orm import GoalRow


class GoalRepository:
    """Zero-setup in-memory adapter used when DATABASE_URL is absent."""

    def __init__(self) -> None:
        self._store: dict[str, Goal] = {}

    def save(self, goal: Goal) -> Goal:
        self._store[goal.goal_id] = goal
        return goal

    def get(self, goal_id: str) -> Goal | None:
        return self._store.get(goal_id)

    def list_by_traveller(
        self,
        traveller_id: str,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Goal]:
        goals = [
            goal for goal in self._store.values()
            if goal.traveller_id == traveller_id
        ]
        return goals[offset:] if limit is None else goals[offset:offset + limit]

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


class SqlAlchemyGoalRepository:
    """Persistent Goal adapter sharing Tralvana's configured SQLAlchemy stack."""

    def __init__(self, factory: sessionmaker[Session]) -> None:
        self._factory = factory

    def save(self, goal: Goal) -> Goal:
        with self._factory.begin() as session:
            session.merge(_row(goal))
        return goal

    def get(self, goal_id: str) -> Goal | None:
        with self._factory() as session:
            row = session.get(GoalRow, goal_id)
            return _entity(row) if row else None

    def list_by_traveller(
        self,
        traveller_id: str,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Goal]:
        with self._factory() as session:
            statement = (
                select(GoalRow)
                .where(GoalRow.traveller_id == traveller_id)
                .order_by(GoalRow.created_at, GoalRow.goal_id)
                .offset(offset)
            )
            if limit is not None:
                statement = statement.limit(limit)
            rows = session.scalars(statement).all()
            return [_entity(row) for row in rows]

    def update(self, goal_id: str, updates: dict[str, Any]) -> Goal | None:
        with self._factory.begin() as session:
            row = session.get(GoalRow, goal_id)
            if row is None:
                return None
            for key, value in updates.items():
                if hasattr(row, key) and value is not None:
                    setattr(row, key, value)
            session.flush()
            return _entity(row)

    def delete(self, goal_id: str) -> bool:
        with self._factory.begin() as session:
            row = session.get(GoalRow, goal_id)
            if row is None:
                return False
            session.delete(row)
            return True


def build_goal_repository():
    url = database_url()
    if not url:
        return GoalRepository()
    engine = create_engine_from_url(url)
    return SqlAlchemyGoalRepository(create_session_factory(engine))


def _row(goal: Goal) -> GoalRow:
    return GoalRow(**goal.to_dict())


def _entity(row: GoalRow) -> Goal:
    return Goal(
        goal_id=row.goal_id,
        traveller_id=row.traveller_id,
        title=row.title,
        goal_type=row.goal_type,
        priority=row.priority,
        budget=dict(row.budget),
        timeframe=dict(row.timeframe),
        travellers=dict(row.travellers),
        interests=list(row.interests),
        constraints=list(row.constraints),
        success_criteria=list(row.success_criteria),
        flexibility=dict(row.flexibility),
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
