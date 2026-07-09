from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import health, traveller, conversation
from app.domains.goals.router import router as goals_router
from app.domains.trips.router import router as trips_router
from app.domains.flights.router import router as flights_router
from app.domains.accommodation.router import router as accommodation_router
from app.demo.demo_router import router as demo_router

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
app.include_router(conversation.router)
app.include_router(goals_router)
app.include_router(trips_router)
app.include_router(flights_router)
app.include_router(accommodation_router)
app.include_router(demo_router)


@app.get("/")
async def root():
    return {"message": "Tralvana API", "status": "running"}
