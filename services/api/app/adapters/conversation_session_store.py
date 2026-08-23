"""PostgreSQL/SQLAlchemy adapter for account-owned planner memory."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from ai.concierge.conversation_session import (
    ConversationSession,
    deserialize_session,
    serialize_session,
)
from ai.concierge.session_store import InMemorySessionStore
from app.database.session import (
    create_engine_from_url,
    create_session_factory,
    database_url,
)
from app.domains.conversation.orm import ConversationSessionRow


class SqlAlchemySessionStore(InMemorySessionStore):
    """Durable implementation of the AI SessionStore protocol."""

    def __init__(self, factory: sessionmaker[Session]) -> None:
        self._factory = factory

    def save(self, session: ConversationSession) -> None:
        with self._factory.begin() as database:
            database.merge(
                ConversationSessionRow(
                    conversation_id=session.conversation_id,
                    traveller_id=session.traveller_id,
                    trip_id=session.trip_id,
                    payload=serialize_session(session),
                    created_at=session.created_at,
                    updated_at=session.updated_at,
                )
            )

    def get(self, conversation_id: str) -> ConversationSession | None:
        with self._factory() as database:
            row = database.get(ConversationSessionRow, conversation_id)
            return deserialize_session(row.payload) if row else None

    def find_by_trip_id(self, trip_id: str) -> ConversationSession | None:
        with self._factory() as database:
            row = database.scalar(
                select(ConversationSessionRow)
                .where(ConversationSessionRow.trip_id == trip_id)
                .order_by(ConversationSessionRow.updated_at.desc())
            )
            return deserialize_session(row.payload) if row else None

    def list_by_traveller(
        self, traveller_id: str, limit: int = 50
    ) -> list[ConversationSession]:
        with self._factory() as database:
            rows = database.scalars(
                select(ConversationSessionRow)
                .where(ConversationSessionRow.traveller_id == traveller_id)
                .order_by(ConversationSessionRow.updated_at.desc())
                .limit(limit)
            ).all()
            return [deserialize_session(row.payload) for row in rows]


def build_persistent_session_store():
    url = database_url()
    if not url:
        return None
    engine = create_engine_from_url(url)
    return SqlAlchemySessionStore(create_session_factory(engine))
