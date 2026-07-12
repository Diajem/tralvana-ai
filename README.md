# Tralvana AI

AI-native travel operating system.

## Structure

```
tralvana-ai/
├── apps/
│   └── web/          # Next.js 15 frontend
├── services/
│   └── api/          # FastAPI backend
├── ai/
│   ├── agents/         # Specialist agents (flight, hotel, budget, visa, experience) —
│   │                   #   still live for MODIFY_TRIP/DESTINATION_QUESTION/TRAVEL_ADVICE/BUDGET_ADVICE
│   ├── concierge/      # Intent classifier, decision engine, conversation engine
│   ├── discovery/      # Six Discovery Layer modules (flights, accommodation, destinations,
│   │                   #   budget, visa, weather)
│   ├── trip_brain/     # Trip Brain — orchestrates the six Discovery modules for PLAN_TRIP
│   ├── explainability/ # Explainability Engine — traveller-facing drivers/trade-offs/confidence
│   ├── intelligence/   # Traveller DNA, knowledge graph
│   ├── manager/        # TravelManager orchestrator
│   ├── memory/         # Traveller intelligence service
│   ├── planning/       # Trip planner, itinerary builder, budget estimator
│   ├── registry/       # Agent registry
│   └── tests/          # AI unit tests
├── travelos/           # Platform layer (SDK, events, config, logging, DI)
│   ├── intelligence_gateway/  # Provider-access infrastructure — contract, registry,
│   │                   #   selection, cache, retry, failover, rate limiting
│   └── live_providers/ # Reusable base for a real vendor integration — auth,
│                       #   transport, request/response mapping, error model,
│                       #   health/tracing/metrics. Includes DuffelFlightProvider
│                       #   (adapters/), the first real vendor adapter, and
│                       #   HttpxTransport, the first real (non-fake) Transport —
│                       #   verified with one live Duffel SANDBOX call (T-037),
│                       #   but not registered by default in the running app
│                       #   (see docs/FIRST_LIVE_PROVIDER.md).
├── docs/               # Architecture docs, ADRs, task tracker
└── docker-compose.yml
```

## Getting Started

### Frontend (apps/web)

```bash
cd apps/web
npm install
npm run dev
# → http://localhost:3000
```

### Backend (services/api)

```bash
cd services/api
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
# → http://localhost:8000
```

### Docker (all services)

```bash
cp .env.example .env
docker-compose up --build
```

## Tests

Install test dependencies (once):

```bash
pip install pytest httpx
```

Run all tests from the project root:

```bash
pytest
# 92 tests — 30 backend API + 62 AI layer
```

Run by suite:

```bash
pytest services/api/tests/    # backend endpoints
pytest ai/tests/              # AI classifiers and planner
pytest travelos/tests/        # platform layer (Intelligence Gateway)
```

No external services required — all tests run against in-memory stores.

See [`docs/TESTING_FRAMEWORK.md`](docs/TESTING_FRAMEWORK.md) for full details.

## CI

GitHub Actions runs `pytest` (required), plus Ruff and frontend lint/build (advisory — see [`docs/TECHNICAL_DEBT_REGISTER.md`](docs/TECHNICAL_DEBT_REGISTER.md) TD-016/TD-017) on every push and pull request to `main`.

See [`docs/CI_CD.md`](docs/CI_CD.md) for full details.
