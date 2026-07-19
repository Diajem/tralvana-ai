from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.database.session import create_engine_from_url, create_session_factory, database_url
from app.domains.commercial.repository import SqlAlchemyCommercialRepository

router = APIRouter(prefix="/internal/commercial", tags=["internal"])


class CommercialStatusResponse(BaseModel):
    configured: bool
    reachable: bool
    schema_version: str
    counts: dict[str, int]


@router.get("/status", response_model=CommercialStatusResponse)
def commercial_status() -> CommercialStatusResponse:
    """Safe, read-only readiness signal. Connection details are never returned."""
    url = database_url()
    empty = {name: 0 for name in ("partners", "programmes", "clicks", "conversions", "commissions")}
    if not url:
        return CommercialStatusResponse(
            configured=False, reachable=False, schema_version="unconfigured", counts=empty
        )

    engine = create_engine_from_url(url)
    factory = create_session_factory(engine)
    try:
        with factory() as session:
            session.execute(text("SELECT 1"))
            counts = SqlAlchemyCommercialRepository(session).counts()
        return CommercialStatusResponse(
            configured=True, reachable=True, schema_version="0001", counts=counts
        )
    except Exception:
        return CommercialStatusResponse(
            configured=True, reachable=False, schema_version="unknown", counts=empty
        )
    finally:
        engine.dispose()
