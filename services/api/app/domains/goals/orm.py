from __future__ import annotations

from sqlalchemy import JSON, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class GoalRow(Base):
    __tablename__ = "travel_goals"

    goal_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    traveller_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    goal_type: Mapped[str] = mapped_column(String(40), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    budget: Mapped[dict] = mapped_column(JSON, nullable=False)
    timeframe: Mapped[dict] = mapped_column(JSON, nullable=False)
    travellers: Mapped[dict] = mapped_column(JSON, nullable=False)
    interests: Mapped[list] = mapped_column(JSON, nullable=False)
    constraints: Mapped[list] = mapped_column(JSON, nullable=False)
    success_criteria: Mapped[list] = mapped_column(JSON, nullable=False)
    flexibility: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(40), nullable=False)
