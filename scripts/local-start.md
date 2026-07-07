# Local Development — Start Guide

## Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Node.js | 22+ | `node -v` |
| Python | 3.12+ | `python --version` |
| npm | 10+ | `npm -v` |
| Docker (optional) | 24+ | `docker -v` |

## Option A — Run Services Individually

### 1. Environment

```bash
# From repo root
cp .env.example .env
# Edit .env and fill in any required keys
```

### 2. Frontend

```bash
cd apps/web
npm install
npm run dev
# → http://localhost:3000
```

### 3. Backend

```bash
cd services/api

# Create and activate virtual environment
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start server with auto-reload
uvicorn app.main:app --reload --port 8000
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

## Option B — Docker Compose

```bash
# From repo root
cp .env.example .env
docker-compose up --build
# Frontend → http://localhost:3000
# Backend  → http://localhost:8000
```

## Verify Everything Is Running

```bash
# Backend health check
curl http://localhost:8000/health
# Expected: {"status": "ok"}

# Frontend
# Open http://localhost:3000 in browser
```

## Common Issues

| Problem | Fix |
|---------|-----|
| Port 3000 in use | `npx kill-port 3000` |
| Port 8000 in use | `npx kill-port 8000` |
| Python venv not activated | Run the activate command above |
| Module not found (Python) | Run `pip install -r requirements.txt` again |
| `npm install` errors | Delete `node_modules/` and retry |
