from __future__ import annotations

from sqlalchemy import JSON, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class TripPlanRow(Base):
    __tablename__ = "trip_plans"

    trip_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    traveller_id: Mapped[str | None] = mapped_column(String(100), index=True)
    goal_id: Mapped[str | None] = mapped_column(String(36), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    origin: Mapped[str] = mapped_column(String(150), nullable=False)
    destination: Mapped[str] = mapped_column(String(150), nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    budget: Mapped[dict] = mapped_column(JSON, nullable=False)
    travellers: Mapped[dict] = mapped_column(JSON, nullable=False)
    interests: Mapped[list] = mapped_column(JSON, nullable=False)
    travel_style: Mapped[str] = mapped_column(String(30), nullable=False)
    assumptions: Mapped[list] = mapped_column(JSON, nullable=False)
    missing_information: Mapped[list] = mapped_column(JSON, nullable=False)
    recommended_destinations: Mapped[list] = mapped_column(JSON, nullable=False)
    draft_itinerary: Mapped[list] = mapped_column(JSON, nullable=False)
    estimated_budget_breakdown: Mapped[dict] = mapped_column(JSON, nullable=False)
    risks: Mapped[list] = mapped_column(JSON, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(40), nullable=False)
    recommended_agents: Mapped[list] = mapped_column(JSON, nullable=False)
    next_actions: Mapped[list] = mapped_column(JSON, nullable=False)
    trip_summary: Mapped[str] = mapped_column(Text, nullable=False)
