from fastapi import APIRouter, Response, status
from pydantic import BaseModel

from app.database.readiness import EXPECTED_SCHEMA_VERSION, inspect_database_readiness

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health_check():
    return {"status": "ok"}


class ReadinessResponse(BaseModel):
    status: str
    database_reachable: bool
    schema_version: str
    expected_schema_version: str
    affiliate_programmes: int


@router.get("/ready", response_model=ReadinessResponse)
def readiness_check(response: Response) -> ReadinessResponse:
    """Deployment gate: database, migrations, and affiliate seed must be ready."""
    database = inspect_database_readiness()
    if not database.ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadinessResponse(
        status="ok" if database.ready else "not_ready",
        database_reachable=database.reachable,
        schema_version=database.schema_version,
        expected_schema_version=EXPECTED_SCHEMA_VERSION,
        affiliate_programmes=database.counts["programmes"],
    )
