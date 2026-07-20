import { cn } from "@/lib/utils";
import type { Sentiment } from "@/types";

const SENTIMENT_CONFIG: Record<Sentiment, { label: string; className: string }> = {
  BULLISH: { label: "Bullish", className: "border-accent/30 bg-accent-dim text-accent" },
  BEARISH: { label: "Bearish", className: "border-danger/30 bg-danger-dim text-danger" },
  NEUTRAL: { label: "Neutral", className: "border-border-strong bg-white/[0.04] text-muted-foreground" },
};

export function SentimentBadge({ sentiment, className }: { sentiment: Sentiment; className?: string }) {
  const config = SENTIMENT_CONFIG[sentiment];
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
        config.className,
        className,
      )}
    >
      {config.label}
    </span>
  );
}
