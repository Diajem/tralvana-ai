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
│   ├── agents/       # Specialist agents (flight, hotel, budget, visa, experience)
│   ├── concierge/    # Intent classifier, decision engine, conversation engine
│   ├── intelligence/ # Traveller DNA, knowledge graph
│   ├── manager/      # TravelManager orchestrator
│   ├── memory/       # Traveller intelligence service
│   ├── orchestration/ # Workflow orchestration
│   ├── planning/     # Trip planner, itinerary builder, budget estimator
│   ├── registry/     # Agent registry
│   └── tests/        # AI unit tests
├── travelos/         # Platform layer (SDK, events, config, logging, DI)
├── docs/             # Architecture docs, ADRs, task tracker
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
```

No external services required — all tests run against in-memory stores.

See [`docs/TESTING_FRAMEWORK.md`](docs/TESTING_FRAMEWORK.md) for full details.
