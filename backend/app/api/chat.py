from datetime import UTC, datetime

from fastapi import APIRouter

from app import mock_data
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/messages", response_model=ChatMessageResponse)
def send_message(request: ChatMessageRequest) -> ChatMessageResponse:
    return ChatMessageResponse(
        role="assistant",
        content=mock_data.get_chat_stub_response(),
        created_at=datetime.now(UTC).isoformat(),
    )
