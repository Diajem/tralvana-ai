# TravelOS Dependency Injection

TravelOS uses a lightweight `ServiceContainer` to manage dependencies between services without hardcoding them.

## ServiceContainer

Located at `travelos/shared/container.py`.

### Registration

```python
from travelos.shared import ServiceContainer

container = ServiceContainer()

# Register a pre-built instance
container.register("logger", my_logger)
container.register("config", my_config)

# Register a lazy singleton (factory called once on first resolve)
container.singleton("db", lambda c: Database(c.resolve("config")))
container.singleton("goal_service", lambda c: GoalService(c.resolve("db")))
```

### Resolution

```python
goal_service = container.resolve("goal_service")

# Safe resolution (returns None if not registered)
logger = container.resolve_or_none("logger")

# Check registration
container.has("goal_service")   # â†’ True
container.registered()          # â†’ ["config", "db", "goal_service", "logger"]
```

### Child Containers

```python
# Child inherits all parent registrations but can override
child = container.child()
child.register("db", test_db)   # override for tests
```

### Reset (for tests)

```python
container.reset()  # clears all registrations
```

## Default Container

A shared default container is provided:

```python
from travelos.shared import default_container

default_container.register("event_bus", event_bus)
```

## ServiceRegistry vs ServiceContainer

| | `ServiceRegistry` | `ServiceContainer` |
|-|-------------------|--------------------|
| **Purpose** | Discover the 7 known TravelOS services | Wire arbitrary dependencies |
| **Resolution** | By canonical service name (`"goal_service"`) | By any string key |
| **Default loaders** | Pre-wired to existing singletons | Empty â€” you register everything |
| **Use when** | Accessing platform services | Building new services with injected deps |

## Wiring Example

```python
from travelos.shared import ServiceContainer
from travelos.logging.travel_logger import TravelLogger
from travelos.events.event_bus import event_bus
from travelos.config.configuration_manager import config

def build_container() -> ServiceContainer:
    c = ServiceContainer()
    c.register("config", config)
    c.register("event_bus", event_bus)
    c.singleton("logger", lambda _: TravelLogger.for_service("App"))
    return c

container = build_container()
```

## Sprint 3+ Notes

The `ServiceContainer` is intentionally simple â€” no autowiring, no annotations, no framework. If the project grows to 30+ services, evaluate `dependency-injector` or `lagom`. Until then, explicit registration is the least surprising approach.
