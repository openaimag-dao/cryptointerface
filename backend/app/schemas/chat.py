from typing import Literal

from pydantic import BaseModel

ChatRole = Literal["user", "assistant"]


class ChatMessageRequest(BaseModel):
    content: str
    session_id: str | None = None


class ChatMessageResponse(BaseModel):
    role: ChatRole
    content: str
    created_at: str
