from datetime import UTC, datetime

from fastapi import APIRouter

from app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from app.services.claude_chat import ChatTurn, send_chat_message

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/messages", response_model=ChatMessageResponse)
async def send_message(request: ChatMessageRequest) -> ChatMessageResponse:
    history = [ChatTurn(role=turn.role, content=turn.content) for turn in request.history]
    content = await send_chat_message(request.content, history)
    return ChatMessageResponse(
        role="assistant",
        content=content,
        created_at=datetime.now(UTC).isoformat(),
    )
