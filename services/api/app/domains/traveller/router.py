"""Traveller profile HTTP routes."""

from fastapi import APIRouter, Depends, HTTPException

from app.auth import AuthenticatedTraveller, require_authenticated_traveller
from app.auth.dependencies import require_owner
from app.domains.traveller.schemas import (
    CreateProfileRequest,
    TravellerProfileResponse,
)
from app.domains.traveller.service import traveller_service

router = APIRouter(prefix="/traveller", tags=["traveller"])


@router.post("/profile", response_model=TravellerProfileResponse, status_code=201)
async def create_profile(
    request: CreateProfileRequest,
    principal: AuthenticatedTraveller | None = Depends(require_authenticated_traveller),
) -> dict:
    return traveller_service.create_profile(
        request,
        traveller_id=principal.user_id if principal else None,
    )


@router.get("/profile/{traveller_id}", response_model=TravellerProfileResponse)
async def get_profile(
    traveller_id: str,
    principal: AuthenticatedTraveller | None = Depends(require_authenticated_traveller),
) -> dict:
    require_owner(principal, traveller_id)
    profile = traveller_service.get_profile(traveller_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
