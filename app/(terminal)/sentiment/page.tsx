"use client";

import { useState } from "react";

import { WATCHLIST_SYMBOLS } from "@/lib/constants";
import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/common/page-header";
import { Button } from "@/components/ui/button";
import { SentimentOverview } from "@/components/sentiment/sentiment-overview";
import { SentimentBreakdown } from "@/components/sentiment/sentiment-breakdown";

export default function SentimentPage() {
  const [symbol, setSymbol] = useState(WATCHLIST_SYMBOLS[0]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Sentiment"
        description="Technical, macro, liquidation, news, and whale signals blended into one read"
      />

      <div className="flex flex-wrap gap-2">
        {WATCHLIST_SYMBOLS.map((s) => (
          <Button
            key={s}
            variant="secondary"
            className={cn("h-8 px-3 text-xs", s === symbol && "border-accent/40 bg-accent-dim text-accent")}
            onClick={() => setSymbol(s)}
          >
            {s}
          </Button>
        ))}
      </div>

      <SentimentOverview symbol={symbol} />
      <SentimentBreakdown symbol={symbol} />
    </div>
  );
}
