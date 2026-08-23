from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ConversationSessionRow(Base):
    __tablename__ = "conversation_sessions"

    conversation_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    traveller_id: Mapped[str | None] = mapped_column(String(100), index=True)
    trip_id: Mapped[str | None] = mapped_column(String(36), index=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(String(40), nullable=False)
    updated_at: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
