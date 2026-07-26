"""T-035 conversation-session persistence contract."""

from __future__ import annotations

import asyncio
import json
from datetime import date
from decimal import Decimal
from typing import Any

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError

from ai.concierge.conversation_engine import ConversationEngine
from ai.concierge.conversation_session import (
    SESSION_SCHEMA_VERSION,
    ConversationSession,
    deserialize_session,
    serialize_session,
)
from ai.concierge.session_store import (
    InMemorySessionStore,
    RedisSessionStore,
    SessionStoreUnavailableError,
    build_session_store,
)
from ai.shared.agent_result import AgentResult
from ai.shared.agent_status import AgentStatus
from ai.trip_brain.models import UnifiedRecommendation


class FakePipeline:
    def __init__(self, client: FakeRedis) -> None:
        self.client = client
        self.commands: list[tuple[str, tuple[Any, ...], dict[str, Any]]] = []

    def __enter__(self) -> FakePipeline:
        return self

    def __exit__(self, *_args: Any) -> None:
        return None

    def set(self, *args: Any, **kwargs: Any) -> FakePipeline:
        self.commands.append(("set", args, kwargs))
        return self

    def delete(self, *args: Any, **kwargs: Any) -> FakePipeline:
        self.commands.append(("delete", args, kwargs))
        return self

    def execute(self) -> list[Any]:
        return [
            getattr(self.client, method)(*args, **kwargs)
            for method, args, kwargs in self.commands
        ]


class FakeRedis:
    def __init__(self, *, ping_error: Exception | None = None) -> None:
        self.values: dict[str, str] = {}
        self.expiries: dict[str, int] = {}
        self.deleted: list[str] = []
        self.ping_error = ping_error

    def ping(self) -> bool:
        if self.ping_error:
            raise self.ping_error
        return True

    def get(self, key: str) -> str | None:
        return self.values.get(key)

    def set(self, key: str, value: str, *, ex: int | None = None) -> bool:
        self.values[key] = value
        if ex is not None:
            self.expiries[key] = ex
        return True

    def delete(self, *keys: str) -> int:
        removed = 0
        for key in keys:
            self.deleted.append(key)
            removed += int(self.values.pop(key, None) is not None)
            self.expiries.pop(key, None)
        return removed

    def pipeline(self, *, transaction: bool) -> FakePipeline:
        assert transaction is True
        return FakePipeline(self)


def _full_session() -> ConversationSession:
    store = InMemorySessionStore()
    session = store.create("traveller-1")
    session.trip_id = "trip-1"
    session.goal_id = "goal-1"
    session.active_goal = "PLAN_TRIP"
    session.pending_questions = ["Which airport?"]
    session.planning_entities = {"destination": "New York", "dates": "7-22 August"}
    session.context_summary = "Two adults travelling from Leeds."
    session.add_message("user", "Plan New York", "PLAN_TRIP")
    session.last_recommendation = UnifiedRecommendation(
        results=[
            AgentResult(
                agent_name="event_intelligence",
                status=AgentStatus.SUCCESS,
                confidence=0.91,
                data={
                    "event_date": date(2026, 8, 15),
                    "estimated_cost": Decimal("45.50"),
                },
                assumptions=["Ticket availability can change."],
                risks=["Verify the official listing."],
                recommendations=["NYCFC"],
                next_actions=["Open official link"],
            )
        ],
        modules_selected=["event_intelligence"],
        modules_succeeded=["event_intelligence"],
        overall_confidence=0.91,
        synthesis_note="One grounded event.",
        conflicts=[],
        explanation={"confidence": 0.91, "drivers": ["travel dates"]},
        destination="New York",
    )
    return session


def test_session_json_round_trip_preserves_complete_planner_state():
    restored = deserialize_session(serialize_session(_full_session()))

    assert restored.conversation_id
    assert restored.traveller_id == "traveller-1"
    assert restored.trip_id == "trip-1"
    assert restored.goal_id == "goal-1"
    assert restored.planning_entities["destination"] == "New York"
    assert restored.history[0].intent == "PLAN_TRIP"
    assert restored.last_recommendation is not None
    assert restored.last_recommendation.destination == "New York"
    result = restored.last_recommendation.results[0]
    assert result.status is AgentStatus.SUCCESS
    assert result.data["event_date"] == "2026-08-15"
    assert result.data["estimated_cost"] == "45.50"


@pytest.mark.parametrize(
    "payload",
    [
        "{}",
        json.dumps({"schema_version": SESSION_SCHEMA_VERSION + 1}),
        json.dumps({"schema_version": SESSION_SCHEMA_VERSION, "conversation_id": ""}),
        "[]",
    ],
)
def test_session_json_rejects_malformed_or_unsupported_records(payload):
    with pytest.raises(ValueError):
        deserialize_session(payload)


def test_in_memory_store_keeps_existing_contract():
    store = InMemorySessionStore()
    created = store.create()
    restored = store.get_or_create(created.conversation_id, "traveller-2")
    restored.trip_id = "trip-2"
    store.save(restored)

    assert restored is created
    assert restored.traveller_id == "traveller-2"
    assert store.find_by_trip_id("trip-2") is created
    assert store.get_or_create("unknown", "traveller-3").conversation_id != "unknown"


def test_redis_store_survives_adapter_recreation_and_sets_both_ttls():
    client = FakeRedis()
    first_worker = RedisSessionStore(client, ttl_seconds=3600)
    session = _full_session()
    first_worker.save(session)

    second_worker = RedisSessionStore(client, ttl_seconds=3600)
    restored = second_worker.get(session.conversation_id)

    assert restored is not None
    assert restored.history[0].content == "Plan New York"
    assert second_worker.find_by_trip_id("trip-1") == restored
    assert client.expiries[f"tralvana:conversation:{session.conversation_id}"] == 3600
    assert client.expiries["tralvana:conversation:trip:trip-1"] == 3600


def test_redis_store_replaces_obsolete_trip_index_atomically():
    client = FakeRedis()
    store = RedisSessionStore(client, ttl_seconds=3600)
    session = _full_session()
    store.save(session)

    session.trip_id = "trip-2"
    store.save(session)

    assert "tralvana:conversation:trip:trip-1" not in client.values
    assert store.find_by_trip_id("trip-2") is not None


def test_redis_store_discards_corrupt_session_without_crashing():
    client = FakeRedis()
    key = "tralvana:conversation:broken"
    client.values[key] = "{not-json"
    store = RedisSessionStore(client, ttl_seconds=60)

    assert store.get("broken") is None
    assert key in client.deleted


def test_redis_store_removes_stale_trip_index():
    client = FakeRedis()
    client.values["tralvana:conversation:trip:trip-gone"] = "missing-conversation"
    store = RedisSessionStore(client, ttl_seconds=60)

    assert store.find_by_trip_id("trip-gone") is None
    assert "tralvana:conversation:trip:trip-gone" in client.deleted


def test_two_conversation_engines_continue_one_session_through_redis():
    client = FakeRedis()
    first_worker = ConversationEngine(RedisSessionStore(client, ttl_seconds=3600))
    first = asyncio.run(first_worker.process("Hello"))

    second_worker = ConversationEngine(RedisSessionStore(client, ttl_seconds=3600))
    second = asyncio.run(
        second_worker.process("Tell me about travel", conversation_id=first["conversation_id"])
    )

    restored = second_worker.get_session(first["conversation_id"])
    assert second["conversation_id"] == first["conversation_id"]
    assert restored is not None
    assert [message.role for message in restored.history] == [
        "user",
        "assistant",
        "user",
        "assistant",
    ]


def test_build_store_defaults_to_memory_without_redis_url(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)

    assert isinstance(build_session_store(), InMemorySessionStore)


def test_build_store_uses_redis_only_after_successful_ping(monkeypatch):
    client = FakeRedis()
    monkeypatch.setenv("REDIS_URL", "redis://private.invalid:6379/0")
    monkeypatch.setattr("redis.Redis.from_url", lambda *_args, **_kwargs: client)

    store = build_session_store()

    assert isinstance(store, RedisSessionStore)


def test_build_store_fails_clearly_when_configured_redis_is_unreachable(monkeypatch):
    secret_url = "redis://user:never-log-this@private.invalid:6379/0"
    client = FakeRedis(ping_error=RedisConnectionError("connection failed"))
    monkeypatch.setenv("REDIS_URL", secret_url)
    monkeypatch.setattr("redis.Redis.from_url", lambda *_args, **_kwargs: client)

    with pytest.raises(SessionStoreUnavailableError) as error:
        build_session_store()

    assert "unavailable" in str(error.value)
    assert secret_url not in str(error.value)
