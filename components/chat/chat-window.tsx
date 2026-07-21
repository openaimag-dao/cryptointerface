"use client";

import { useEffect, useRef } from "react";
import { Bot, Sparkles } from "lucide-react";

import { CHAT_SUGGESTIONS } from "@/lib/mock/chat";
import { useChatStore } from "@/store/chat-store";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { ChatMessage } from "@/components/chat/chat-message";
import { ChatInput } from "@/components/chat/chat-input";

export function ChatWindow() {
  const sessions = useChatStore((state) => state.sessions);
  const activeSessionId = useChatStore((state) => state.activeSessionId);
  const isStreaming = useChatStore((state) => state.isStreaming);
  const sendMessage = useChatStore((state) => state.sendMessage);
  const bottomRef = useRef<HTMLDivElement>(null);

  const activeSession = sessions.find((session) => session.id === activeSessionId);
  const messages = activeSession?.messages ?? [];

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  return (
    <div className="flex h-full flex-1 flex-col">
      <ScrollArea className="flex-1">
        <div className="mx-auto flex max-w-3xl flex-col gap-5 px-6 py-6">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center gap-4 py-16 text-center">
              <div className="flex size-14 items-center justify-center rounded-2xl border border-accent/30 bg-accent-dim text-accent">
                <Bot className="size-6" />
              </div>
              <div>
                <h2 className="text-lg font-semibold text-foreground">AIMAG AI Assistant</h2>
                <p className="mt-1 max-w-sm text-sm text-muted-foreground">
                  Ask about market conditions or AI signals — answers are grounded in the live watchlist snapshot.
                </p>
              </div>
              <div className="grid w-full max-w-lg grid-cols-1 gap-2 sm:grid-cols-2">
                {CHAT_SUGGESTIONS.map((suggestion) => (
                  <Button
                    key={suggestion}
                    variant="secondary"
                    className="h-auto justify-start whitespace-normal px-3.5 py-2.5 text-left text-xs font-normal text-muted-foreground hover:text-foreground"
                    onClick={() => void sendMessage(suggestion)}
                  >
                    <Sparkles className="size-3.5 shrink-0 text-accent" />
                    {suggestion}
                  </Button>
                ))}
              </div>
            </div>
          ) : (
            messages.map((message) => <ChatMessage key={message.id} message={message} />)
          )}

          {isStreaming ? (
            <div className="flex items-center gap-2 pl-11 text-xs text-muted-foreground">
              <span className="flex gap-1">
                <span className="size-1.5 animate-bounce rounded-full bg-accent [animation-delay:-0.3s]" />
                <span className="size-1.5 animate-bounce rounded-full bg-accent [animation-delay:-0.15s]" />
                <span className="size-1.5 animate-bounce rounded-full bg-accent" />
              </span>
              AIMAG AI is thinking...
            </div>
          ) : null}

          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      <div className="mx-auto w-full max-w-3xl">
        <ChatInput />
      </div>
    </div>
  );
}
