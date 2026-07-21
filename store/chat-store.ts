import { create } from "zustand";

import { createEmptyChatSession } from "@/lib/mock/chat";
import { sendChatMessage } from "@/services/chat-service";
import type { ChatMessage, ChatSession } from "@/types";

function createId(): string {
  return Math.random().toString(36).slice(2, 10);
}

interface ChatState {
  sessions: ChatSession[];
  activeSessionId: string;
  isStreaming: boolean;
  setActiveSession: (id: string) => void;
  createSession: () => void;
  sendMessage: (content: string) => Promise<void>;
}

const initialSessions = [createEmptyChatSession()];

export const useChatStore = create<ChatState>((set, get) => ({
  sessions: initialSessions,
  activeSessionId: initialSessions[0]?.id ?? "",
  isStreaming: false,

  setActiveSession: (id) => set({ activeSessionId: id }),

  createSession: () => {
    const newSession: ChatSession = {
      id: createId(),
      title: "New conversation",
      updatedAt: new Date().toISOString(),
      messages: [],
    };
    set((state) => ({
      sessions: [newSession, ...state.sessions],
      activeSessionId: newSession.id,
    }));
  },

  sendMessage: async (content) => {
    const trimmed = content.trim();
    if (!trimmed) return;

    const priorMessages = get().sessions.find((session) => session.id === get().activeSessionId)?.messages ?? [];

    const userMessage: ChatMessage = {
      id: createId(),
      role: "user",
      content: trimmed,
      createdAt: new Date().toISOString(),
    };

    set((state) => ({
      sessions: state.sessions.map((session) =>
        session.id === state.activeSessionId
          ? {
              ...session,
              title: session.messages.length === 0 ? trimmed.slice(0, 48) : session.title,
              messages: [...session.messages, userMessage],
              updatedAt: new Date().toISOString(),
            }
          : session,
      ),
      isStreaming: true,
    }));

    let responseContent: string;
    try {
      responseContent = await sendChatMessage(trimmed, priorMessages);
    } catch {
      responseContent = "Something went wrong reaching the AI assistant. Please try again.";
    }

    const assistantMessage: ChatMessage = {
      id: createId(),
      role: "assistant",
      content: responseContent,
      createdAt: new Date().toISOString(),
    };

    set((state) => ({
      sessions: state.sessions.map((session) =>
        session.id === state.activeSessionId
          ? {
              ...session,
              messages: [...session.messages, assistantMessage],
              updatedAt: new Date().toISOString(),
            }
          : session,
      ),
      isStreaming: false,
    }));
  },
}));
