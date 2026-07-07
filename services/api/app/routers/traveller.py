from fastapi import APIRouter, HTTPException

from app.models.traveller import CreateProfileRequest, TravellerProfileResponse
from app.services import traveller_service

router = APIRouter(prefix="/traveller", tags=["traveller"])


@router.post("/profile", response_model=TravellerProfileResponse, status_code=201)
async def create_profile(request: CreateProfileRequest) -> dict:
    return traveller_service.create_profile(request)


@router.get("/profile/{traveller_id}", response_model=TravellerProfileResponse)
async def get_profile(traveller_id: str) -> dict:
    profile = traveller_service.get_profile(traveller_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile
