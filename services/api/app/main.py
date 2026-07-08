from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import health, traveller
from app.conversation.conversation_router import router as conversation_router
from app.domains.goals.router import router as goals_router

app = FastAPI(title="Tralvana API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(traveller.router)
app.include_router(conversation_router)
app.include_router(goals_router)


@app.get("/")
async def root():
    return {"message": "Tralvana API", "status": "running"}
