from typing import Literal

from app.schemas.base import CamelModel

ChatRole = Literal["user", "assistant"]


class ChatHistoryItem(CamelModel):
    role: ChatRole
    content: str


class ChatMessageRequest(CamelModel):
    content: str
    session_id: str | None = None
    # Prior turns of the active session, oldest first, so Claude has
    # conversation context. Sessions live client-side only (see
    # store/chat-store.ts) — the backend stays stateless between requests.
    history: list[ChatHistoryItem] = []


class ChatMessageResponse(CamelModel):
    role: ChatRole
    content: str
    created_at: str
