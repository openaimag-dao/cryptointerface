import { apiFetch } from "@/lib/api-client";
import type { ChatMessage } from "@/types";

interface ChatMessageResponse {
  role: "assistant";
  content: string;
  createdAt: string;
}

export async function sendChatMessage(content: string, history: ChatMessage[]): Promise<string> {
  const response = await apiFetch<ChatMessageResponse>("/api/chat/messages", {
    method: "POST",
    body: JSON.stringify({
      content,
      history: history.map(({ role, content: historyContent }) => ({ role, content: historyContent })),
    }),
  });
  return response.content;
}
