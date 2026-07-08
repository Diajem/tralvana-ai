# TravelOS Logging

`TravelLogger` provides structured, service-aware logging across all TravelOS services.

## Usage

```python
from travelos.logging import TravelLogger

logger = TravelLogger.for_service("GoalService")

logger.info("Goal created", goal_id="abc-123", status="DRAFT")
logger.warning("Low confidence score", score=0.42, goal_id="abc-123")
logger.error("Repository write failed", goal_id="abc-123")
logger.debug("Entity resolved from cache", entity_type="City", name="Tokyo")

# Exceptions
try:
    ...
except Exception as exc:
    logger.exception("Unexpected failure", exc, goal_id="abc-123")
```

## Log Format

```
[2026-07-08T12:00:00Z] [INFO    ] [travelos.GoalService] Goal created | goal_id=abc-123 | status=DRAFT
```

Fields:
- `[timestamp]` â€” UTC ISO 8601
- `[LEVEL]` â€” INFO / WARNING / ERROR / DEBUG (padded to 8 chars)
- `[travelos.ServiceName]` â€” hierarchical logger name
- Message, then `| key=value` context pairs

## Log Levels

| Level | Method | When to use |
|-------|--------|-------------|
| `DEBUG` | `logger.debug()` | Detailed diagnostic information |
| `INFO` | `logger.info()` | Normal operational events (created, resolved, completed) |
| `WARNING` | `logger.warning()` | Unexpected-but-handled situations (fallback used, low confidence) |
| `ERROR` | `logger.error()` | Failures that affect the response |

## Level Configuration

The active level is read from `ConfigurationManager.log_level`, which reads from `LOG_LEVEL` env var with environment-specific defaults:

| Environment | Default Level |
|-------------|--------------|
| development | DEBUG |
| test | WARNING |
| production | INFO |

Override at runtime:
```bash
export LOG_LEVEL=ERROR
```

## Service Naming Convention

Always use the class name:

```python
# In GoalService:
self._logger = TravelLogger.for_service("GoalService")

# In TripPlanningService:
self._logger = TravelLogger.for_service("TripPlanningService")
```

This keeps log lines easily filterable by service:
```bash
# Filter to goal service logs only
grep "travelos.GoalService" app.log
```

## BaseService Integration

Services that extend `BaseService` get a logger automatically:

```python
from travelos.shared import BaseService

class MyService(BaseService):
    def do_thing(self):
        self.logger.info("Doing thing")
```

## Output

Logs are written to `stdout`. In production, collect stdout with your log aggregator (Datadog, Grafana Loki, CloudWatch).
