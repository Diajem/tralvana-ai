from fastapi import APIRouter, HTTPException

from app.domains.visa.schemas import CheckVisaRequest, VisaAssessmentResponse
from app.domains.visa.service import visa_intelligence_service

router = APIRouter(tags=["visa"])


@router.post("/visa/check", response_model=VisaAssessmentResponse, status_code=201)
async def check_visa(request: CheckVisaRequest) -> dict:
    trip = None
    if request.trip_id:
        try:
            from app.domains.trips.service import trip_planning_service
            trip = trip_planning_service.get(request.trip_id)
        except Exception:
            pass

    return visa_intelligence_service.check(request, trip=trip)


@router.get("/visa/{visa_assessment_id}", response_model=VisaAssessmentResponse)
async def get_visa_assessment(visa_assessment_id: str) -> dict:
    assessment = visa_intelligence_service.get(visa_assessment_id)
    if not assessment:
        raise HTTPException(status_code=404, detail="Visa assessment not found")
    return assessment


@router.get("/trips/{trip_id}/visa", response_model=list[VisaAssessmentResponse])
async def list_trip_visa(trip_id: str) -> list[dict]:
    return visa_intelligence_service.list_by_trip(trip_id)
