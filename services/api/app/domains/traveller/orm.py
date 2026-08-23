from __future__ import annotations

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class TravellerProfileRow(Base):
    __tablename__ = "traveller_profiles"

    traveller_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(40), nullable=False)
    identity: Mapped[dict] = mapped_column(JSON, nullable=False)
    preferences: Mapped[dict] = mapped_column(JSON, nullable=False)
    loyalty: Mapped[dict] = mapped_column(JSON, nullable=False)
    travel_history: Mapped[list] = mapped_column(JSON, nullable=False)
