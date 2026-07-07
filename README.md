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
│   ├── agents/       # Agent definitions
│   ├── orchestration/ # Workflow orchestration
│   └── memory/       # Memory layer
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
