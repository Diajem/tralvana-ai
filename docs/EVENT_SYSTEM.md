# TravelOS Event System

The TravelOS event system decouples services using domain events and a synchronous event bus.

## Core Classes

### DomainEvent

Base class for all events. Every event has:
- `event_id` â€” unique UUID
- `occurred_at` â€” UTC ISO timestamp
- `event_type` â€” the class name (e.g. `"GoalCreated"`)
- `payload` â€” optional dict for additional context

### EventBus

Synchronous, in-process pub/sub bus. Handlers are called in registration order.

## Built-in Events

| Event | Fields | Trigger |
|-------|--------|---------|
| `TravellerCreated` | `traveller_id`, `name`, `home_city`, `nationality` | Traveller profile created |
| `GoalCreated` | `goal_id`, `traveller_id`, `goal_type`, `title` | Goal created via API or conversation |
| `TripPlanned` | `trip_id`, `traveller_id`, `destination`, `duration_days`, `status`, `confidence` | Trip plan generated |
| `ConversationStarted` | `conversation_id`, `traveller_id` | New conversation session started |
| `ConversationCompleted` | `conversation_id`, `intent`, `confidence`, `trip_id` | Conversation turn completed |
| `KnowledgeUpdated` | `entity_type`, `entity_id`, `update_type` | KG entity added / updated / removed |

## Usage

### Publishing

```python
from travelos.events import event_bus, GoalCreated

event_bus.publish(GoalCreated(
    goal_id="abc-123",
    traveller_id="xyz-456",
    goal_type="football_travel",
    title="Football & Food Tour â€” Japan",
))
```

### Subscribing

```python
from travelos.events import event_bus, GoalCreated
from travelos.events.domain_event import DomainEvent

# Subscribe to a specific event
def on_goal_created(event: GoalCreated) -> None:
    print(f"New goal: {event.title}")

event_bus.subscribe(GoalCreated, on_goal_created)

# Subscribe to all events (wildcard)
def log_all(event: DomainEvent) -> None:
    print(event.event_type, event.event_id)

event_bus.subscribe_all(log_all)
```

### Unsubscribing

```python
event_bus.unsubscribe(GoalCreated, on_goal_created)
```

### Introspection

```python
event_bus.all_subscriptions()
# â†’ {"GoalCreated": 2, "*": 1}

event_bus.subscribers(GoalCreated)
# â†’ [<function on_goal_created>]
```

## Guarantees

- Handler exceptions are caught and logged â€” they never crash the publisher
- Each `publish()` call returns the number of handlers invoked
- Call `event_bus.clear()` to remove all handlers (useful in tests)

## Adding Custom Events

```python
from dataclasses import dataclass
from travelos.events.domain_event import DomainEvent

@dataclass
class BookingRequested(DomainEvent):
    booking_ref: str = ""
    provider: str = ""

# Then publish normally
event_bus.publish(BookingRequested(booking_ref="BA123", provider="British Airways"))
```

## Sprint 3+ Evolution

The `EventBus` is designed for easy replacement:

```python
# Sprint 3: swap implementation, keep the same publish/subscribe API
class RedisEventBus(EventBus):
    async def publish_async(self, event: DomainEvent) -> int:
        ...
```

The interface contract stays the same â€” all callers continue working.
