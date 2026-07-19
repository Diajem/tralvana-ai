# Local Development — Start Guide

## Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Node.js | 22+ | `node -v` |
| Python | 3.12+ | `python --version` |
| npm | 10+ | `npm -v` |
| Docker (optional) | 24+ | `docker -v` |

## Recommended — Windows PowerShell

From the repository root:

```powershell
.\scripts\start-local.ps1
```

This opens the API and web app in separate PowerShell windows. The first API
run creates `.venv` and installs the pinned Python dependencies. The first web
run installs the locked npm dependencies.

- Web: http://localhost:3001
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

To run either service by itself:

```powershell
.\scripts\start-api.ps1
.\scripts\start-web.ps1
```

## Option A — Run Services Individually (macOS/Linux)

### 1. Environment

```bash
# From repo root
cp .env.example .env
# Edit .env and fill in any required keys
```

### 2. Frontend

```bash
cd apps/web
npm ci
npm run dev:local
# → http://localhost:3001
```

### 3. Backend

```bash
python -m venv .venv

source .venv/bin/activate

# Install dependencies
pip install -r services/api/requirements.txt

# Start server with auto-reload
PYTHONPATH=.:services/api python -m uvicorn app.main:app --app-dir services/api --reload --port 8000
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

## Option B — Docker Compose

```bash
# From repo root
cp .env.example .env
docker compose up --build
# Frontend → http://localhost:3001
# Backend  → http://localhost:8000
# PostgreSQL → localhost:5432; migrations run before API startup
```

When running the API outside Docker and using commercial persistence, start a
PostgreSQL instance, set `DATABASE_URL`, and apply migrations first:

```bash
PYTHONPATH=.:services/api python -m alembic -c services/api/alembic.ini upgrade head
```

## Verify Everything Is Running

```bash
# Backend health check
curl http://localhost:8000/health
# Expected: {"status": "ok"}

# Frontend
# Open http://localhost:3001 in browser
```

## Common Issues

| Problem | Fix |
|---------|-----|
| Port 3001 in use | Run `.\scripts\start-web.ps1 -Port 3002` |
| Port 8000 in use | `npx kill-port 8000` |
| Python venv not activated | Run the activate command above |
| Module not found (Python) | Start from the repository root with `scripts/start-api.ps1` |
| `npm ci` errors | Delete `node_modules/` and retry |
