from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/conversation", tags=["conversation"])


class ConversationMessageRequest(BaseModel):
    traveller_id: str | None = None
    message: str
    conversation_id: str | None = None


class ConversationMessageResponse(BaseModel):
    conversation_id: str
    intent: str
    response: str
    confidence: float
    assumptions: list[str]
    missing_information: list[str]
    next_actions: list[str]
    recommended_agents: list[str]
    goal_id: str | None = None
    trip_id: str | None = None


@router.post("/message", response_model=ConversationMessageResponse)
async def conversation_message(request: ConversationMessageRequest) -> dict:
    from ai.concierge.travel_concierge import travel_concierge
    return await travel_concierge.handle(
        request.message,
        traveller_id=request.traveller_id,
        conversation_id=request.conversation_id,
    )
