"use client";

import { BrainCircuit } from "lucide-react";

import { timeAgo } from "@/lib/utils";
import { useDashboardIntelligence } from "@/hooks/use-dashboard-intelligence";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { DirectionBadge } from "@/components/common/direction-badge";

interface IntelligenceCardProps {
  symbol: string;
}

function ScoreCell({ label, score }: { label: string; score: number }) {
  const tone = score >= 65 ? "text-accent" : score <= 35 ? "text-danger" : "text-warning";
  return (
    <div className="rounded-lg border border-border-subtle bg-white/[0.02] p-3">
      <p className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className={`mt-1 font-tabular text-lg font-semibold ${tone}`}>{Math.round(score)}</p>
    </div>
  );
}

export function IntelligenceCard({ symbol }: IntelligenceCardProps) {
  const { data: intelligence, isLoading } = useDashboardIntelligence(symbol);

  if (isLoading || !intelligence) {
    return (
      <Card className="p-5">
        <Skeleton className="h-48 w-full rounded-lg" />
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-1.5 text-foreground">
          <BrainCircuit className="size-4 text-accent" />
          Market Intelligence
        </CardTitle>
        <div className="flex items-center gap-2">
          <DirectionBadge direction={intelligence.direction} size="sm" />
          <span className="text-xs text-muted-foreground">Updated {timeAgo(intelligence.lastUpdated)}</span>
        </div>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-3 sm:grid-cols-6">
          <ScoreCell label="Market Score" score={intelligence.overallScore} />
          <ScoreCell label="Sentiment" score={intelligence.sentimentScore} />
          <ScoreCell label="Macro" score={intelligence.macroScore} />
          <ScoreCell label="News" score={intelligence.newsScore} />
          <ScoreCell label="Whales" score={intelligence.whaleScore} />
          <ScoreCell label="Liquidations" score={intelligence.liquidationScore} />
        </div>

        {intelligence.aiExplanation ? (
          <div className="mt-4 rounded-lg border border-border-subtle bg-white/[0.02] p-4">
            <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">AI Explanation</p>
            <p className="mt-2 text-sm leading-relaxed text-foreground/90">{intelligence.aiExplanation.summary}</p>
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
