from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import health, conversation, explain, internal, planner
from app.domains.traveller.router import router as traveller_router
from app.domains.goals.router import router as goals_router
from app.domains.trips.router import router as trips_router
from app.domains.flights.router import router as flights_router
from app.domains.accommodation.router import router as accommodation_router
from app.domains.destinations.router import router as destinations_router
from app.domains.budget.router import router as budget_router
from app.domains.visa.router import router as visa_router
from app.domains.weather.router import router as weather_router
from app.domains.events.router import router as events_router
from app.demo.demo_router import router as demo_router
from app.domains.commercial.router import public_router as commercial_public_router
from app.domains.commercial.router import router as commercial_router
from travelos.live_providers.accommodation_provider_bootstrap import configure_accommodation_provider
from travelos.live_providers.event_provider_bootstrap import configure_event_provider
from travelos.live_providers.flight_provider_bootstrap import configure_flight_provider
from travelos.config import config
from ai.ports import configure_planning_port
from app.adapters.planning_adapter import PlanningAdapter
from app.auth.config import AuthSettings
from app.auth.dependencies import require_authenticated_traveller
from app.adapters.conversation_session_store import build_persistent_session_store
from ai.concierge.conversation_engine import conversation_engine

# Composition root (T-038, extended T-039) — the one place that decides
# whether Duffel gets registered for real. A no-op in MOCK mode (the
# default, for both); in LIVE_SANDBOX mode without DUFFEL_API_TOKEN,
# this fails the process at startup rather than serving requests from a
# mode it can't actually fulfil. See docs/LIVE_FLIGHT_SEARCH.md and
# docs/LIVE_ACCOMMODATION_SEARCH.md.
configure_flight_provider()
configure_accommodation_provider()
configure_event_provider()
configure_planning_port(PlanningAdapter())
_persistent_session_store = build_persistent_session_store()
if _persistent_session_store is not None:
    conversation_engine.configure_store(_persistent_session_store)
if config.is_production:
    # Fail closed before the server accepts traffic. Production must never
    # fall back to the zero-setup local/test authentication mode.
    AuthSettings.from_environment()

app = FastAPI(title="Tralvana API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(demo_router)
app.include_router(commercial_public_router)

_authenticated = [Depends(require_authenticated_traveller)]
app.include_router(traveller_router, dependencies=_authenticated)
app.include_router(conversation.router, dependencies=_authenticated)
app.include_router(explain.router, dependencies=_authenticated)
app.include_router(planner.router, dependencies=_authenticated)
app.include_router(internal.router, dependencies=_authenticated)
app.include_router(goals_router, dependencies=_authenticated)
app.include_router(trips_router, dependencies=_authenticated)
app.include_router(flights_router, dependencies=_authenticated)
app.include_router(accommodation_router, dependencies=_authenticated)
app.include_router(destinations_router, dependencies=_authenticated)
app.include_router(budget_router, dependencies=_authenticated)
app.include_router(visa_router, dependencies=_authenticated)
app.include_router(weather_router, dependencies=_authenticated)
app.include_router(events_router, dependencies=_authenticated)
app.include_router(commercial_router, dependencies=_authenticated)


@app.get("/")
async def root():
    return {"message": "Tralvana API", "status": "running"}
