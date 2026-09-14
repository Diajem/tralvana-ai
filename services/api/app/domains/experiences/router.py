from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.auth import AuthenticatedTraveller, require_authenticated_traveller
from app.domains.experiences.schemas import (
    ExperienceDetailsResponse,
    ExperienceSearchRequest,
    ExperienceSearchResponse,
)
from app.domains.experiences.service import experience_discovery_service
from travelos.intelligence_gateway.exceptions import ProviderError

router = APIRouter(prefix="/experiences", tags=["experiences"])


@router.post("/search", response_model=ExperienceSearchResponse)
async def search_experiences(
    request: ExperienceSearchRequest,
    principal: AuthenticatedTraveller | None = Depends(
        require_authenticated_traveller
    ),
) -> dict:
    del principal
    try:
        return experience_discovery_service.search(
            destination=request.destination,
            start_date=request.start_date.isoformat() if request.start_date else None,
            end_date=request.end_date.isoformat() if request.end_date else None,
            currency=request.currency,
            count=request.count,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ProviderError as exc:
        raise HTTPException(
            status_code=503,
            detail="Viator sandbox experiences are temporarily unavailable",
        ) from exc


@router.get("/{product_code}", response_model=ExperienceDetailsResponse)
async def get_experience(
    product_code: str,
    currency: str = Query(default="GBP", min_length=3, max_length=3),
    include_schedule: bool = True,
    principal: AuthenticatedTraveller | None = Depends(
        require_authenticated_traveller
    ),
) -> dict:
    del principal
    try:
        return experience_discovery_service.details(
            product_code,
            currency=currency.upper(),
            include_schedule=include_schedule,
        )
    except ProviderError as exc:
        raise HTTPException(
            status_code=503,
            detail="Viator sandbox experience details are temporarily unavailable",
        ) from exc
