import type { ChatSession } from "@/types";

export function getMockChatSessions(): ChatSession[] {
  return [
    {
      id: "session-1",
      title: "BTC breakout setup review",
      updatedAt: new Date(Date.now() - 1000 * 60 * 20).toISOString(),
      messages: [
        {
          id: "m1",
          role: "user",
          content: "Is BTC forming a bullish continuation pattern on the 4H?",
          createdAt: new Date(Date.now() - 1000 * 60 * 22).toISOString(),
        },
        {
          id: "m2",
          role: "assistant",
          content:
            "Based on current structure, BTC is consolidating above the daily VWAP with declining volume — consistent with a bull flag. AI Score sits at 76 (LONG bias). This is a placeholder response; live model reasoning will connect in Sprint 2.",
          createdAt: new Date(Date.now() - 1000 * 60 * 21).toISOString(),
        },
      ],
    },
    {
      id: "session-2",
      title: "Portfolio risk check",
      updatedAt: new Date(Date.now() - 1000 * 60 * 60 * 5).toISOString(),
      messages: [],
    },
  ];
}

export const CHAT_SUGGESTIONS = [
  "Summarize today's top market movers",
  "What's the AI Score for SOLUSDT right now?",
  "Explain the current BTC funding rate",
  "Show me the highest confidence LONG signals",
];
