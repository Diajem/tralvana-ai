from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.conversation.conversation_engine import conversation_engine
from app.conversation.response_composer import ResponseComposer

router = APIRouter(prefix="/conversation", tags=["conversation"])
_composer = ResponseComposer()


class StartRequest(BaseModel):
    traveller_id: str | None = None


class StartResponse(BaseModel):
    conversation_id: str
    greeting: str


class MessageRequest(BaseModel):
    message: str


class MessageResponse(BaseModel):
    conversation_id: str
    reply: str
    intent: str
    confidence: float
    entities: dict
    active_goal: str | None
    pending_questions: list[str]


class SessionResponse(BaseModel):
    conversation_id: str
    traveller_id: str | None
    active_goal: str | None
    pending_questions: list[str]
    context_summary: str
    message_count: int
    created_at: str
    updated_at: str


@router.post("/start", response_model=StartResponse, status_code=201)
async def start_conversation(request: StartRequest) -> dict:
    session = conversation_engine.start_session(request.traveller_id)

    traveller_name: str | None = None
    if request.traveller_id:
        try:
            from ai.memory.traveller_intelligence_service import traveller_intelligence_service
            data = traveller_intelligence_service.build_context_data(request.traveller_id)
            if data:
                traveller_name = data.get("identity", {}).get("name")
        except Exception:
            pass

    return {
        "conversation_id": session.conversation_id,
        "greeting": _composer.compose_greeting(traveller_name),
    }


@router.post("/{conversation_id}/message", response_model=MessageResponse)
async def send_message(conversation_id: str, request: MessageRequest) -> dict:
    result = await conversation_engine.process_message(conversation_id, request.message)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


@router.get("/{conversation_id}", response_model=SessionResponse)
async def get_session(conversation_id: str) -> dict:
    session = conversation_engine.get_session(conversation_id)
    if not session:
        raise HTTPException(status_code=404, detail="Conversation not found")
    data = session.to_dict()
    data["message_count"] = len(session.history)
    return data
