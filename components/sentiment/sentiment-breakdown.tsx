"use client";

import { cn } from "@/lib/utils";
import { useSentiment } from "@/hooks/use-sentiment";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { DirectionBadge } from "@/components/common/direction-badge";

interface SentimentBreakdownProps {
  symbol: string;
}

const CATEGORY_LABELS: Record<string, string> = {
  technical: "Technical Analysis",
  macro: "Macro",
  liquidations: "Liquidations",
  news: "News",
  whales: "Whales",
};

// Order matters more than alphabetical here — most-to-least real data
// today (news/whales are still Sprint 4 stubs, see backend README).
const CATEGORY_ORDER = ["technical", "macro", "liquidations", "news", "whales"];

export function SentimentBreakdown({ symbol }: SentimentBreakdownProps) {
  const { data: sentiment, isLoading } = useSentiment(symbol);

  if (isLoading || !sentiment) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 5 }).map((_, index) => (
          <Skeleton key={index} className="h-[180px] rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {CATEGORY_ORDER.map((name) => {
        const category = sentiment.breakdown[name];
        if (!category) return null;
        const isStub = category.confidence === 0 && (name === "news" || name === "whales");

        return (
          <Card key={name} className="p-5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                {CATEGORY_LABELS[name] ?? name}
              </span>
              <DirectionBadge direction={category.direction} size="sm" />
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="font-tabular text-2xl font-semibold text-foreground">
                {Math.round(category.score)}
              </span>
              <span className="text-xs text-muted-foreground">/ 100</span>
            </div>
            <p className={cn("mt-1 text-xs text-muted-foreground", isStub && "italic")}>
              Confidence {Math.round(category.confidence)}%
            </p>
            <ul className="mt-3 space-y-1">
              {category.reasons.slice(0, 3).map((reason) => (
                <li key={reason} className="text-xs leading-relaxed text-foreground/80">
                  • {reason}
                </li>
              ))}
            </ul>
          </Card>
        );
      })}
    </div>
  );
}
