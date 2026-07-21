import type { ChatSession } from "@/types";

export function createEmptyChatSession(): ChatSession {
  return {
    id: "session-1",
    title: "New conversation",
    updatedAt: new Date().toISOString(),
    messages: [],
  };
}

export const CHAT_SUGGESTIONS = [
  "Summarize today's top market movers",
  "What's the AI Score for SOLUSDT right now?",
  "Explain the current BTC funding rate",
  "Show me the highest confidence LONG signals",
];
