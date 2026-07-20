import { motion } from "framer-motion";
import { Bot, User } from "lucide-react";

import { cn } from "@/lib/utils";
import type { ChatMessage as ChatMessageType } from "@/types";

export function ChatMessage({ message }: { message: ChatMessageType }) {
  const isUser = message.role === "user";

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className={cn("flex items-start gap-3", isUser && "flex-row-reverse")}
    >
      <div
        className={cn(
          "flex size-8 shrink-0 items-center justify-center rounded-full border",
          isUser ? "border-border-subtle bg-white/[0.04] text-foreground" : "border-accent/30 bg-accent-dim text-accent",
        )}
      >
        {isUser ? <User className="size-4" /> : <Bot className="size-4" />}
      </div>
      <div
        className={cn(
          "max-w-[75%] rounded-2xl border px-4 py-2.5 text-sm leading-relaxed",
          isUser
            ? "border-border-subtle bg-white/[0.04] text-foreground"
            : "border-accent/20 bg-surface-elevated text-foreground",
        )}
      >
        {message.content}
      </div>
    </motion.div>
  );
}
