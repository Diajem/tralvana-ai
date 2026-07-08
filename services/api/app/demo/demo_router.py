from fastapi import APIRouter

from app.demo.demo_service import demo_service

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/japan-football-food")
async def japan_football_food_demo() -> dict:
    """
    End-to-end TravelOS demo: Japan Football & Food scenario.

    Runs the full pipeline — DNA inference, Goal creation, Goal reasoning,
    Knowledge Graph query, Conversation Engine, Trip Planning — and returns
    one complete response.
    """
    return await demo_service.run()
