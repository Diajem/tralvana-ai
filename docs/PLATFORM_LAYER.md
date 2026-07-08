# TravelOS Platform Layer

T-011 â€” The internal infrastructure layer shared by every TravelOS service.

## Purpose

The platform layer makes TravelOS behave like an operating system, not a collection of services. Every service uses the same logging, configuration, event bus, and type system. No service needs to know where these come from.

## Directory Structure

```
travelos/
â”œâ”€â”€ __init__.py
â”œâ”€â”€ config/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â””â”€â”€ configuration_manager.py    â† Environment config (dev/test/prod)
â”œâ”€â”€ events/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â”œâ”€â”€ domain_event.py             â† DomainEvent base + concrete events
â”‚   â””â”€â”€ event_bus.py                â† Synchronous pub/sub EventBus
â”œâ”€â”€ logging/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â””â”€â”€ travel_logger.py            â† TravelLogger (structured, named)
â”œâ”€â”€ registry/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â””â”€â”€ service_registry.py         â† Service discovery for 7 core services
â”œâ”€â”€ sdk/
â”‚   â”œâ”€â”€ __init__.py
â”‚   â””â”€â”€ travelos_sdk.py             â† TravelOS public SDK (9 methods)
â””â”€â”€ shared/
    â”œâ”€â”€ __init__.py
    â”œâ”€â”€ result.py                   â† Result[T] + Error
    â”œâ”€â”€ identifier.py               â† Identifier (typed UUID)
    â”œâ”€â”€ timestamp.py                â† Timestamp (UTC datetime wrapper)
    â”œâ”€â”€ pagination.py               â† Pagination + Page[T]
    â”œâ”€â”€ base_repository.py          â† BaseRepository[T] ABC
    â”œâ”€â”€ base_service.py             â† BaseService ABC
    â””â”€â”€ container.py               â† ServiceContainer (DI)
```

## Components

| Component | Class | File |
|-----------|-------|------|
| SDK | `TravelOS` | `travelos/sdk/travelos_sdk.py` |
| Service Registry | `ServiceRegistry` | `travelos/registry/service_registry.py` |
| Config | `ConfigurationManager` | `travelos/config/configuration_manager.py` |
| Logger | `TravelLogger` | `travelos/logging/travel_logger.py` |
| Events | `EventBus`, `DomainEvent` | `travelos/events/` |
| DI Container | `ServiceContainer` | `travelos/shared/container.py` |
| Shared types | `Result`, `Error`, `Identifier`, `Timestamp`, `Pagination`, `Page` | `travelos/shared/` |

## Design Principles

1. **No circular imports** â€” platform modules never import from `services/api/app/` or `ai/`. The dependency direction is always: application â†’ platform.
2. **Lazy service resolution** â€” the ServiceRegistry and SDK use lazy imports to avoid startup-time import failures.
3. **Provider-agnostic** â€” Logger wraps stdlib `logging`, Config reads env vars, EventBus is sync now (swap for Redis in Sprint 3).
4. **No external dependencies** â€” the platform layer adds zero new packages to `requirements.txt`.

## Usage

```python
# Get the SDK singleton
from travelos.sdk import travelos

# Log from any service
from travelos.logging import TravelLogger
logger = TravelLogger.for_service("MyService")
logger.info("Something happened", key="value")

# Read config
from travelos.config import config
if config.is_production:
    ...

# Publish an event
from travelos.events import event_bus, GoalCreated
event_bus.publish(GoalCreated(goal_id="abc", traveller_id="xyz", ...))

# Subscribe to events
event_bus.subscribe(GoalCreated, lambda e: print(e.goal_id))

# Use Result[T]
from travelos.shared import Result
result = Result.ok({"id": "123"})
if result:
    data = result.unwrap()
```

## Sprint 3+ Evolution

| Component | Current | Sprint 3 |
|-----------|---------|----------|
| EventBus | In-process sync | Redis Streams / RabbitMQ async |
| ServiceRegistry | Module imports | Service mesh discovery |
| ServiceContainer | Dict-based | Optional: replace with `dependency-injector` |
| Config | Env vars | Vault / AWS Secrets Manager adapter |
