"use client";

import { useState, type KeyboardEvent, type SyntheticEvent } from "react";
import { SendHorizonal } from "lucide-react";

import { useChatStore } from "@/store/chat-store";
import { Button } from "@/components/ui/button";

export function ChatInput() {
  const [value, setValue] = useState("");
  const isStreaming = useChatStore((state) => state.isStreaming);
  const sendMessage = useChatStore((state) => state.sendMessage);

  function handleSubmit(event: SyntheticEvent) {
    event.preventDefault();
    if (!value.trim() || isStreaming) return;
    void sendMessage(value);
    setValue("");
  }

  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSubmit(event);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-2 border-t border-border-subtle p-4">
      <textarea
        value={value}
        onChange={(event) => setValue(event.target.value)}
        onKeyDown={handleKeyDown}
        rows={1}
        placeholder="Ask AIMAG AI about markets, signals, or your portfolio..."
        className="max-h-32 min-h-[42px] flex-1 resize-none rounded-lg border border-border-subtle bg-white/[0.03] px-3.5 py-2.5 text-sm text-foreground outline-none transition-colors placeholder:text-muted-foreground focus-visible:border-accent/50 focus-visible:ring-2 focus-visible:ring-accent/20"
      />
      <Button type="submit" size="icon" disabled={!value.trim() || isStreaming}>
        <SendHorizonal className="size-4" />
      </Button>
    </form>
  );
}
