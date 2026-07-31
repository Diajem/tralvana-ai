from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from app.domains.goals.models import Goal, GoalStatus, GoalType
from app.domains.goals.repository import GoalRepository, build_goal_repository
from app.domains.goals.schemas import CreateGoalRequest, UpdateGoalRequest


class GoalService:
    """
    Goal domain logic layer.

    Sprint 1: in-memory repository + GoalClassifier for auto-classification.
    Sprint 3+: swap repository for PostgreSQL adapter; no service changes needed.
    """

    def __init__(self, repository: GoalRepository) -> None:
        self._repo = repository

    def create(self, request: CreateGoalRequest) -> dict[str, Any]:
        # Auto-classify goal_type if still GENERAL_TRAVEL and we can infer better
        goal_type = request.goal_type
        if goal_type == GoalType.GENERAL_TRAVEL.value and request.interests:
            try:
                from ai.goals.goal_classifier import goal_classifier

                inferred = goal_classifier.classify_from_interests(request.interests)
                if inferred != GoalType.GENERAL_TRAVEL.value:
                    goal_type = inferred
            except Exception:
                pass

        now = datetime.now(timezone.utc).isoformat()
        goal = Goal(
            goal_id=str(uuid.uuid4()),
            traveller_id=request.traveller_id,
            title=request.title,
            goal_type=goal_type,
            priority=request.priority,
            budget=request.budget.model_dump(),
            timeframe=request.timeframe.model_dump(),
            travellers=request.travellers.model_dump(),
            interests=request.interests,
            constraints=request.constraints,
            success_criteria=request.success_criteria,
            flexibility=request.flexibility.model_dump(),
            status=GoalStatus.DRAFT.value,
            created_at=now,
            updated_at=now,
        )
        self._repo.save(goal)
        return goal.to_dict()

    def get(self, goal_id: str) -> dict[str, Any] | None:
        goal = self._repo.get(goal_id)
        return goal.to_dict() if goal else None

    def list_by_traveller(
        self,
        traveller_id: str,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        return [
            goal.to_dict()
            for goal in self._repo.list_by_traveller(
                traveller_id,
                limit=limit,
                offset=offset,
            )
        ]

    def update(self, goal_id: str, request: UpdateGoalRequest) -> dict[str, Any] | None:
        updates: dict[str, Any] = {}
        for field, value in request.model_dump(exclude_none=True).items():
            if (
                field in ("budget", "timeframe", "travellers", "flexibility")
                and value is not None
            ):
                updates[field] = value
            elif value is not None:
                updates[field] = value

        now = datetime.now(timezone.utc).isoformat()
        updates["updated_at"] = now

        goal = self._repo.update(goal_id, updates)
        if not goal:
            return None

        # Auto-promote status if planning-ready
        if goal.status == GoalStatus.DRAFT.value:
            score = self._readiness_score(goal)
            if score >= 0.75:
                goal.status = GoalStatus.ACTIVE.value
            if score >= 0.90:
                goal.status = GoalStatus.READY_FOR_PLANNING.value

        return goal.to_dict()

    def create_from_conversation(
        self,
        traveller_id: str | None,
        message: str,
        entities: dict[str, str],
    ) -> dict[str, Any]:
        """Create a minimal DRAFT goal from a conversation PLAN_TRIP intent."""
        try:
            from ai.goals.goal_classifier import goal_classifier

            goal_type = goal_classifier.classify_from_text(message)
        except Exception:
            goal_type = GoalType.GENERAL_TRAVEL.value

        destination = entities.get("destination", "")
        date_hint = entities.get("date_hint", "")
        interests = [
            value for value in entities.get("interests", "").split(",") if value
        ]
        duration_days = (
            int(entities["duration_days"]) if entities.get("duration_days") else None
        )
        adults = int(entities.get("adults", "1"))
        title = f"Trip to {destination}" if destination else "New Travel Goal"
        budget_amount = (
            float(entities["budget_amount"])
            if entities.get("budget_amount")
            else None
        )
        if budget_amount is not None and budget_amount.is_integer():
            budget_amount = int(budget_amount)
        budget_currency = entities.get("budget_currency", "USD")

        now = datetime.now(timezone.utc).isoformat()
        goal = Goal(
            goal_id=str(uuid.uuid4()),
            traveller_id=traveller_id or "anonymous",
            title=title,
            goal_type=goal_type,
            priority=3,
            budget={
                "min_usd": None,
                "max_usd": None,
                "amount": budget_amount,
                "currency": budget_currency,
                "source": "TRAVELLER_DECLARED" if budget_amount else "NOT_PROVIDED",
            },
            timeframe={
                "earliest": entities.get("start_date"),
                "latest": entities.get("end_date"),
                "duration_days": duration_days,
                "flexible": not bool(entities.get("start_date")),
                "hint": date_hint or None,
                "month": (
                    int(entities["month"]) if entities.get("month") else None
                ),
                "year": (
                    int(entities["travel_year"])
                    if entities.get("travel_year")
                    else None
                ),
                "precision": entities.get("date_precision"),
            },
            travellers={
                "adults": adults,
                "children": int(entities.get("children", "0")),
                "infants": int(entities.get("infants", "0")),
            },
            interests=interests,
            constraints=[],
            success_criteria=[],
            flexibility={"dates": True, "duration": True, "budget": False},
            status=GoalStatus.DRAFT.value,
            created_at=now,
            updated_at=now,
        )
        self._repo.save(goal)
        return goal.to_dict()

    def _readiness_score(self, goal: Goal) -> float:
        score = 0.0
        if goal.title:
            score += 0.15
        if goal.goal_type != GoalType.GENERAL_TRAVEL.value:
            score += 0.10
        b = goal.budget
        if b.get("min_usd") and b.get("max_usd"):
            score += 0.20
        t = goal.timeframe
        if t.get("earliest") and t.get("latest"):
            score += 0.20
        if goal.travellers.get("adults", 0) >= 1:
            score += 0.10
        if goal.interests:
            score += 0.10
        if goal.success_criteria:
            score += 0.10
        if goal.constraints:
            score += 0.05
        return score


_repository = build_goal_repository()
goal_service = GoalService(_repository)
