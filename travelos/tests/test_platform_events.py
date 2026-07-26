from travelos.events.domain_event import (
    ConversationCompleted,
    ConversationStarted,
    DomainEvent,
    GoalCreated,
    KnowledgeUpdated,
    TravellerCreated,
    TripPlanned,
)
from travelos.events.event_bus import EventBus


def test_domain_event_has_unique_identity_utc_timestamp_and_payload():
    first = DomainEvent(payload={"source": "planner"})
    second = DomainEvent()

    assert first.event_id != second.event_id
    assert first.occurred_at.endswith("+00:00")
    assert first.event_type == "DomainEvent"
    assert first.to_dict() == {
        "event_id": first.event_id,
        "event_type": "DomainEvent",
        "occurred_at": first.occurred_at,
        "payload": {"source": "planner"},
    }


def test_concrete_domain_events_add_their_public_fields():
    cases = [
        (
            TravellerCreated(
                traveller_id="traveller-1",
                name="Diajem",
                home_city="Leeds",
                nationality="IE",
            ),
            {"traveller_id": "traveller-1", "name": "Diajem"},
        ),
        (
            GoalCreated(
                goal_id="goal-1",
                traveller_id="traveller-1",
                goal_type="HOLIDAY",
                title="New York",
            ),
            {"goal_id": "goal-1", "goal_type": "HOLIDAY"},
        ),
        (
            TripPlanned(
                trip_id="trip-1",
                destination="New York",
                duration_days=15,
                status="DRAFT",
                confidence=0.9,
            ),
            {"trip_id": "trip-1", "duration_days": 15},
        ),
        (
            ConversationStarted(
                conversation_id="conversation-1",
                traveller_id="traveller-1",
            ),
            {"conversation_id": "conversation-1"},
        ),
        (
            ConversationCompleted(
                conversation_id="conversation-1",
                intent="PLAN_TRIP",
                confidence=0.95,
                trip_id="trip-1",
            ),
            {"intent": "PLAN_TRIP", "trip_id": "trip-1"},
        ),
        (
            KnowledgeUpdated(
                entity_type="City",
                entity_id="new-york",
                update_type="updated",
            ),
            {"entity_type": "City", "update_type": "updated"},
        ),
    ]

    for event, expected in cases:
        payload = event.to_dict()["payload"]
        assert expected.items() <= payload.items()


def test_publish_calls_typed_and_wildcard_handlers_in_order():
    bus = EventBus()
    calls = []
    event = GoalCreated(goal_id="goal-1")

    bus.subscribe(GoalCreated, lambda received: calls.append(("typed", received)))
    bus.subscribe_all(lambda received: calls.append(("wildcard", received)))

    assert bus.publish(event) == 2
    assert calls == [("typed", event), ("wildcard", event)]


def test_string_subscription_unsubscribe_and_introspection():
    bus = EventBus()
    calls = []

    def handler(event):
        calls.append(event)

    bus.subscribe("GoalCreated", handler)
    assert bus.subscribers(GoalCreated) == [handler]
    assert bus.all_subscriptions() == {"GoalCreated": 1}

    bus.unsubscribe(GoalCreated, handler)
    assert bus.publish(GoalCreated()) == 0
    assert calls == []
    assert bus.all_subscriptions() == {}


def test_failing_handler_does_not_stop_later_handlers():
    bus = EventBus()
    calls = []

    def fail(event):
        calls.append("failed")
        raise RuntimeError("handler failed")

    def succeed(event):
        calls.append("succeeded")

    bus.subscribe(GoalCreated, fail)
    bus.subscribe(GoalCreated, succeed)

    assert bus.publish(GoalCreated()) == 1
    assert calls == ["failed", "succeeded"]


def test_publish_uses_subscription_snapshot_and_clear_removes_everything():
    bus = EventBus()
    calls = []

    def late_handler(event):
        calls.append("late")

    def registering_handler(event):
        calls.append("registering")
        bus.subscribe(GoalCreated, late_handler)

    bus.subscribe(GoalCreated, registering_handler)

    assert bus.publish(GoalCreated()) == 1
    assert calls == ["registering"]
    assert bus.publish(GoalCreated()) == 2
    assert calls == ["registering", "registering", "late"]

    bus.clear()
    assert bus.all_subscriptions() == {}
