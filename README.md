# Tralvana AI

AI-native travel operating system.

**Primary experience**: the AI Travel Planner — describe a trip in natural language at `/planner`
(`POST /planner/plan`) and get back one coherent, consultant-style itinerary assembled from Trip
Brain's six Discovery modules. See `docs/AI_TRAVEL_PLANNER.md`.

## Structure

```
tralvana-ai/
├── apps/
│   └── web/          # Next.js 15 frontend
├── services/
│   └── api/          # FastAPI backend, Alembic migrations, commercial ledger
├── ai/
│   ├── agents/         # Specialist agents (flight, hotel, budget, visa, experience) —
│   │                   #   still live for MODIFY_TRIP/DESTINATION_QUESTION/TRAVEL_ADVICE/BUDGET_ADVICE
│   ├── concierge/      # Intent classifier, decision engine, conversation engine
│   ├── discovery/      # Six Discovery Layer modules (flights, accommodation, destinations,
│   │                   #   budget, visa, weather)
│   ├── trip_brain/     # Trip Brain — orchestrates the six Discovery modules for PLAN_TRIP;
│   │                   #   trip_assembly.py (T-040) assembles Trip Brain's own output into
│   │                   #   one consultant-style itinerary, never recalculating any score
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
│                       #   and DuffelStaysProvider (adapters/), HttpxTransport
│                       #   (the first real, non-fake Transport), and
│                       #   {flight,accommodation}_provider_bootstrap.py — the
│                       #   composition-root wiring that turns real Duffel sandbox
│                       #   search on for TRALVANA_FLIGHT_PROVIDER_MODE=LIVE_SANDBOX /
│                       #   TRALVANA_ACCOMMODATION_PROVIDER_MODE=LIVE_SANDBOX (both
│                       #   MOCK by default). See docs/LIVE_FLIGHT_SEARCH.md and
│                       #   docs/LIVE_ACCOMMODATION_SEARCH.md (Stays access not yet
│                       #   granted on this account — see the latter's Status section).
├── scripts/            # Operational scripts — e.g. verify_duffel_live_sandbox.py,
│                       #   verify_duffel_stays_live_sandbox.py — manual (never-in-CI)
│                       #   live sandbox verification
├── docs/               # Architecture docs, ADRs, task tracker
└── docker-compose.yml
```

## Getting Started

### Frontend (apps/web)

```bash
cd apps/web
npm ci
npm run dev:local
# → http://localhost:3001
```

### Backend (run from the repository root)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r services/api/requirements.txt
PYTHONPATH=.:services/api python -m uvicorn app.main:app --app-dir services/api --reload
# → http://localhost:8000
```

On Windows PowerShell, start both services from the repository root:

```powershell
.\scripts\start-local.ps1
```

Tralvana uses port `3001` because port `3000` is reserved for Luxorahut POS.

### Docker (all services)

```bash
cp .env.example .env
docker compose up --build
```

Compose starts PostgreSQL, applies the commercial schema migration, then starts
the API and web app. See [`docs/COMMERCIAL_DATA_FOUNDATION.md`](docs/COMMERCIAL_DATA_FOUNDATION.md).

To load the verified Tralvana affiliate catalogue after migration:

```bash
PYTHONPATH=services/api python services/api/scripts/seed_commercial_catalogue.py
```

See [`docs/SAFE_AFFILIATE_LINKS.md`](docs/SAFE_AFFILIATE_LINKS.md) for disclosure,
allow-listing, click attribution, and the programmes still awaiting tracked links.

## Tests

Install test dependencies (once):

```bash
pip install pytest httpx
```

Run all tests from the project root:

```bash
pytest
# 1,200 tests across API, AI, and TravelOS platform layers
```

Run by suite:

```bash
pytest services/api/tests/    # backend endpoints
pytest ai/tests/              # AI classifiers and planner
pytest travelos/tests/        # platform layer (Intelligence Gateway)
```

No external services are required for tests. Commercial persistence tests use
an isolated SQLite database; deployments use PostgreSQL.

See [`docs/TESTING_FRAMEWORK.md`](docs/TESTING_FRAMEWORK.md) for full details.

## CI

GitHub Actions requires pytest, Ruff, frontend lint, and the frontend production build to pass on every push and pull request to `main`.

See [`docs/CI_CD.md`](docs/CI_CD.md) for full details.
