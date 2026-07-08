# Testing Framework

T-012 — Deterministic test suite for TravelOS backend API and AI layer.

## Overview

| Suite | Location | Tests | Runner |
|-------|----------|------:|--------|
| Backend API | `services/api/tests/` | 30 | `pytest` (FastAPI TestClient) |
| AI Layer | `ai/tests/` | 62 | `pytest` (pure unit) |
| **Total** | | **92** | |

No mocks for external services — the in-memory singletons are fast and deterministic by design.

## Running Tests

```bash
# All tests (from project root)
pytest

# Backend only
pytest services/api/tests/

# AI layer only
pytest ai/tests/

# Verbose with failure detail
pytest -v --tb=short
```

## Configuration

`pytest.ini` at the project root:

```ini
[pytest]
testpaths = services/api/tests ai/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
pythonpath = . services/api
```

`pythonpath = . services/api` makes both the project root (`ai.*`, `travelos.*`) and the API directory (`app.*`) importable without any `sys.path` manipulation.

## Backend API Tests (`services/api/tests/`)

### Fixtures (`conftest.py`)

| Fixture | Scope | Description |
|---------|-------|-------------|
| `client` | session | `TestClient(app)` — reused across all tests |
| `sample_profile` | function | Minimal valid traveller profile dict |
| `sample_goal` | function | Creates a traveller + goal, returns goal dict |

### Test Modules

| Module | Covers | Tests |
|--------|--------|------:|
| `test_health.py` | GET /health, GET / | 2 |
| `test_traveller.py` | POST/GET /traveller/profile | 4 |
| `test_goals.py` | POST/GET /goals, list | 6 |
| `test_conversation.py` | POST /conversation | 5 |
| `test_trips.py` | POST/GET /trips | 6 |
| `test_demo.py` | POST /demo/japan-football-food | 7 |

### Key Assertions

- Status codes (201 created, 200 ok, 404 not found)
- Required fields in responses
- Conversation intent detection
- Trip itinerary length matches `duration_days`
- Budget breakdowns have positive `total_estimate_usd`
- Demo pipeline completes all 7 stages

## AI Layer Tests (`ai/tests/`)

### Fixtures (`conftest.py`)

| Fixture | Description |
|---------|-------------|
| `football_profile` | Alex Okafor — moderate budget, sport/food interests |
| `luxury_profile` | Sophia Laurent — first class, luxury/art interests |
| `sample_goal` | Football & Food tour goal dict (Tokyo, 10 days) |

### Test Modules

| Module | Component | Tests |
|--------|-----------|------:|
| `test_intent_classifier.py` | `IntentClassifier` | 15 |
| `test_decision_engine.py` | `DecisionEngine` | 13 |
| `test_agent_registry.py` | `AgentRegistry` | 10 |
| `test_dna_classifier.py` | `TravellerDNAInferenceService` | 11 |
| `test_trip_planner.py` | `TripPlanner` | 13 |

### Key Assertions

**IntentClassifier**
- Correct intent for each of the 8 intent types
- Entity extraction: destination, date_hint
- GENERAL_CONVERSATION fallback confidence = 1.0
- Case-insensitive matching

**DecisionEngine**
- PLAN_TRIP not ready without destination and date
- Safety-sensitive destinations flagged (`kabul`, `mogadishu`, etc.)
- Agents dispatched only when `has_enough_information = True`

**AgentRegistry**
- Default registry has budget/flight/hotel/experience/visa agents
- Custom registry starts empty, register/get works correctly
- `list_agents()` returns sorted keys

**TravellerDNA**
- Confidence 0.0–1.0
- All traits bounded 0.0–1.0
- Luxury profile scores higher on `luxury_orientation`
- Football profile scores higher on `adventure_seeking`

**TripPlanner**
- Itinerary length matches `duration_days`
- First day = arrival, last day = departure
- Budget `total_estimate_usd` > 0
- No recommended destinations when destination is known
- Recommended destinations populated when destination is empty

## Dependencies

```
pytest==8.3.4
httpx==0.28.1       # required by FastAPI TestClient
fastapi             # already in services/api/requirements.txt
uvicorn             # already in services/api/requirements.txt
pydantic            # already in services/api/requirements.txt
```

Install: `pip install pytest httpx`

## Design Decisions

**No mock objects** — All services use in-memory singletons. Mocking them would test the test scaffolding, not the code. The in-memory stores reset when the process exits, so tests are isolated at the session level.

**sync TestClient** — FastAPI's `TestClient` wraps async route handlers in a synchronous interface. No `pytest-asyncio` needed for backend tests.

**Single `pytest.ini`** — Both suites collect under one config with `pythonpath` to avoid sys.path collisions between `app.*` (API) and `ai.*` imports.

**Deterministic AI tests** — All AI modules are rule-based in Sprint 1, making them fully deterministic. No LLMs, no network calls, no randomness.
