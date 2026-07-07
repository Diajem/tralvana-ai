# Platform Architecture

## System Diagram

```
┌─────────────────────────────────────────────────────┐
│                   Browser / Client                  │
│              apps/web  (Next.js 15)                 │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP / WebSocket
┌──────────────────────▼──────────────────────────────┐
│               API Gateway                           │
│           services/api  (FastAPI)                   │
│  /health   /trips   /agents   /profile              │
└──────────────────────┬──────────────────────────────┘
                       │ Python function calls
┌──────────────────────▼──────────────────────────────┐
│              AI Orchestration Layer                 │
│         ai/orchestration/orchestrator.py            │
│                                                     │
│   ┌─────────────────┐   ┌────────────────────────┐  │
│   │ TravelManager   │   │  (future agents)       │  │
│   │ Agent           │   │  FlightSearch          │  │
│   │                 │   │  HotelSearch           │  │
│   └────────┬────────┘   └────────────────────────┘  │
└────────────┼────────────────────────────────────────┘
             │
┌────────────▼────────────────────────────────────────┐
│              Memory Layer                           │
│           ai/memory/  (schema-defined)              │
│         Traveller profiles, trip history            │
└─────────────────────────────────────────────────────┘
```

## Services

| Service | Tech | Port | Responsibility |
|---------|------|------|----------------|
| `apps/web` | Next.js 15 | 3000 | UI, routing, auth |
| `services/api` | FastAPI | 8000 | REST API, agent dispatch |
| `ai/` | Python | — | Agent logic, orchestration |

## Communication

- Frontend → API: REST (JSON)
- API → Orchestrator: Direct Python import (same process, Sprint 0)
- Orchestrator → Agents: Async function calls

## Deployment (Sprint 0)

Local only. Docker Compose wires both services. No cloud infra yet.

## Future Additions

- Message queue (Redis / RabbitMQ) between API and orchestrator
- Vector store for memory persistence
- Auth layer (Clerk or NextAuth)
