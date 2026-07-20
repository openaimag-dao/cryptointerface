"use client";

import { MessageSquarePlus } from "lucide-react";

import { cn, timeAgo } from "@/lib/utils";
import { useChatStore } from "@/store/chat-store";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";

export function ChatSidebar() {
  const sessions = useChatStore((state) => state.sessions);
  const activeSessionId = useChatStore((state) => state.activeSessionId);
  const setActiveSession = useChatStore((state) => state.setActiveSession);
  const createSession = useChatStore((state) => state.createSession);

  return (
    <div className="flex h-full w-64 shrink-0 flex-col border-r border-border-subtle">
      <div className="p-3">
        <Button variant="secondary" className="w-full justify-start gap-2" onClick={createSession}>
          <MessageSquarePlus className="size-4" />
          New conversation
        </Button>
      </div>
      <ScrollArea className="flex-1 px-2">
        <div className="space-y-1 pb-3">
          {sessions.map((session) => (
            <button
              key={session.id}
              type="button"
              onClick={() => setActiveSession(session.id)}
              className={cn(
                "w-full rounded-lg px-3 py-2.5 text-left transition-colors hover:bg-white/[0.05]",
                session.id === activeSessionId && "bg-accent-dim",
              )}
            >
              <p
                className={cn(
                  "truncate text-sm font-medium",
                  session.id === activeSessionId ? "text-accent" : "text-foreground",
                )}
              >
                {session.title}
              </p>
              <p className="mt-0.5 text-xs text-muted-foreground">
                {session.messages.length > 0 ? timeAgo(session.updatedAt) : "No messages yet"}
              </p>
            </button>
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
