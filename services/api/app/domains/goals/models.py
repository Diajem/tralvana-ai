from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class GoalType(str, Enum):
    RELAXATION = "RELAXATION"
    ADVENTURE = "ADVENTURE"
    FOOTBALL_TRAVEL = "FOOTBALL_TRAVEL"
    FAMILY_TRIP = "FAMILY_TRIP"
    BUSINESS_TRAVEL = "BUSINESS_TRAVEL"
    FOOD_TOUR = "FOOD_TOUR"
    PHOTOGRAPHY = "PHOTOGRAPHY"
    PILGRIMAGE = "PILGRIMAGE"
    DIASPORA_TRAVEL = "DIASPORA_TRAVEL"
    ROMANTIC_TRIP = "ROMANTIC_TRIP"
    GENERAL_TRAVEL = "GENERAL_TRAVEL"


class GoalStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    READY_FOR_PLANNING = "READY_FOR_PLANNING"
    PLANNED = "PLANNED"
    ARCHIVED = "ARCHIVED"


@dataclass
class Goal:
    goal_id: str
    traveller_id: str
    title: str
    goal_type: str                           # GoalType value
    priority: int                            # 1 = highest
    budget: dict                             # {min_usd, max_usd, currency}
    timeframe: dict                          # {earliest, latest, duration_days, flexible}
    travellers: dict                         # {adults, children, infants}
    interests: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    success_criteria: list[str] = field(default_factory=list)
    flexibility: dict = field(default_factory=lambda: {"dates": True, "duration": True, "budget": False})
    status: str = GoalStatus.DRAFT.value
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return {
            "goal_id": self.goal_id,
            "traveller_id": self.traveller_id,
            "title": self.title,
            "goal_type": self.goal_type,
            "priority": self.priority,
            "budget": self.budget,
            "timeframe": self.timeframe,
            "travellers": self.travellers,
            "interests": self.interests,
            "constraints": self.constraints,
            "success_criteria": self.success_criteria,
            "flexibility": self.flexibility,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
