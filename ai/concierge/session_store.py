"""Conversation session persistence adapters."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Protocol

from ai.concierge.conversation_session import (
    ConversationSession,
    deserialize_session,
    serialize_session,
)
from travelos.config import config

SESSION_KEY_PREFIX = "tralvana:conversation:"
TRIP_INDEX_KEY_PREFIX = "tralvana:conversation:trip:"


class SessionStore(Protocol):
    def create(self, traveller_id: str | None = None) -> ConversationSession: ...

    def get_or_create(
        self,
        conversation_id: str | None,
        traveller_id: str | None,
    ) -> ConversationSession: ...

    def save(self, session: ConversationSession) -> None: ...

    def get(self, conversation_id: str) -> ConversationSession | None: ...

    def find_by_trip_id(self, trip_id: str) -> ConversationSession | None: ...

    def list_by_traveller(
        self, traveller_id: str, limit: int = 50
    ) -> list[ConversationSession]: ...


class SessionStoreUnavailableError(RuntimeError):
    """The explicitly configured external session store cannot be reached."""


class InMemorySessionStore:
    """Zero-setup adapter for local development and deterministic tests."""

    def __init__(self) -> None:
        self._sessions: dict[str, ConversationSession] = {}

    def create(self, traveller_id: str | None = None) -> ConversationSession:
        session = _new_session(traveller_id)
        self.save(session)
        return session

    def get_or_create(
        self,
        conversation_id: str | None,
        traveller_id: str | None,
    ) -> ConversationSession:
        session = self.get(conversation_id) if conversation_id else None
        if session is None:
            return self.create(traveller_id)
        if traveller_id and not session.traveller_id:
            session.traveller_id = traveller_id
        return session

    def save(self, session: ConversationSession) -> None:
        self._sessions[session.conversation_id] = session

    def get(self, conversation_id: str) -> ConversationSession | None:
        return self._sessions.get(conversation_id)

    def find_by_trip_id(self, trip_id: str) -> ConversationSession | None:
        return next((s for s in self._sessions.values() if s.trip_id == trip_id), None)

    def list_by_traveller(
        self, traveller_id: str, limit: int = 50
    ) -> list[ConversationSession]:
        sessions = [
            session for session in self._sessions.values()
            if session.traveller_id == traveller_id
        ]
        sessions.sort(key=lambda session: session.updated_at, reverse=True)
        return sessions[:limit]


class RedisSessionStore:
    """Redis-backed store with TTL and an O(1) trip-to-conversation index."""

    def __init__(self, client: Any, ttl_seconds: int) -> None:
        if ttl_seconds <= 0:
            raise ValueError("conversation session TTL must be greater than zero")
        self._client = client
        self._ttl_seconds = ttl_seconds

    def create(self, traveller_id: str | None = None) -> ConversationSession:
        session = _new_session(traveller_id)
        self.save(session)
        return session

    def get_or_create(
        self,
        conversation_id: str | None,
        traveller_id: str | None,
    ) -> ConversationSession:
        session = self.get(conversation_id) if conversation_id else None
        if session is None:
            return self.create(traveller_id)
        if traveller_id and not session.traveller_id:
            session.traveller_id = traveller_id
        return session

    def save(self, session: ConversationSession) -> None:
        previous = self.get(session.conversation_id)
        session_key = self._session_key(session.conversation_id)
        with self._client.pipeline(transaction=True) as pipeline:
            if previous and previous.trip_id and previous.trip_id != session.trip_id:
                pipeline.delete(self._trip_key(previous.trip_id))
            pipeline.set(
                session_key,
                serialize_session(session),
                ex=self._ttl_seconds,
            )
            if session.trip_id:
                pipeline.set(
                    self._trip_key(session.trip_id),
                    session.conversation_id,
                    ex=self._ttl_seconds,
                )
            pipeline.execute()

    def get(self, conversation_id: str) -> ConversationSession | None:
        key = self._session_key(conversation_id)
        payload = self._client.get(key)
        if payload is None:
            return None
        try:
            session = deserialize_session(payload)
        except (UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
            self._client.delete(key)
            return None
        if session.conversation_id != conversation_id:
            self._client.delete(key)
            return None
        return session

    def find_by_trip_id(self, trip_id: str) -> ConversationSession | None:
        index_key = self._trip_key(trip_id)
        conversation_id = self._client.get(index_key)
        if conversation_id is None:
            return None
        if isinstance(conversation_id, bytes):
            conversation_id = conversation_id.decode("utf-8")
        session = self.get(str(conversation_id))
        if session is None or session.trip_id != trip_id:
            self._client.delete(index_key)
            return None
        return session

    def list_by_traveller(
        self, traveller_id: str, limit: int = 50
    ) -> list[ConversationSession]:
        sessions: list[ConversationSession] = []
        for key in self._client.scan_iter(match=f"{SESSION_KEY_PREFIX}*"):
            if isinstance(key, bytes):
                key = key.decode("utf-8")
            conversation_id = str(key)[len(SESSION_KEY_PREFIX):]
            session = self.get(conversation_id)
            if session is not None and session.traveller_id == traveller_id:
                sessions.append(session)
        sessions.sort(key=lambda session: session.updated_at, reverse=True)
        return sessions[:limit]

    @staticmethod
    def _session_key(conversation_id: str) -> str:
        return f"{SESSION_KEY_PREFIX}{conversation_id}"

    @staticmethod
    def _trip_key(trip_id: str) -> str:
        return f"{TRIP_INDEX_KEY_PREFIX}{trip_id}"


def build_session_store() -> SessionStore:
    """Select Redis only when explicitly configured; never infer a backend."""
    redis_url = config.redis_url
    if not redis_url:
        return InMemorySessionStore()

    try:
        from redis import Redis
        from redis.exceptions import RedisError
    except ImportError as exc:
        raise SessionStoreUnavailableError(
            "REDIS_URL is configured but the Redis client is not installed"
        ) from exc

    try:
        client = Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=config.redis_socket_timeout_seconds,
            socket_timeout=config.redis_socket_timeout_seconds,
            health_check_interval=30,
        )
        client.ping()
    except (RedisError, ValueError):
        raise SessionStoreUnavailableError(
            "REDIS_URL is configured but the session store is unavailable"
        ) from None
    return RedisSessionStore(client, config.conversation_session_ttl_seconds)


def _new_session(traveller_id: str | None) -> ConversationSession:
    now = datetime.now(timezone.utc).isoformat()
    return ConversationSession(
        conversation_id=str(uuid.uuid4()),
        created_at=now,
        updated_at=now,
        traveller_id=traveller_id,
    )
