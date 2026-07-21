"use client";

import { useSentiment } from "@/hooks/use-sentiment";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { DirectionBadge } from "@/components/common/direction-badge";
import { AiScoreRing } from "@/components/common/ai-score-ring";

interface SentimentOverviewProps {
  symbol: string;
}

export function SentimentOverview({ symbol }: SentimentOverviewProps) {
  const { data: sentiment, isLoading } = useSentiment(symbol);

  if (isLoading || !sentiment) {
    return (
      <Card className="p-5">
        <Skeleton className="h-28 w-full rounded-lg" />
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="text-foreground">Overall Sentiment</CardTitle>
        <span className="text-xs text-muted-foreground">{symbol}</span>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4">
          <AiScoreRing score={Math.round(sentiment.overallScore)} size={64} strokeWidth={4} />
          <div>
            <DirectionBadge direction={sentiment.direction} />
            <p className="mt-1.5 font-tabular text-xs text-muted-foreground">
              Confidence <span className="text-foreground">{Math.round(sentiment.confidence)}%</span>
            </p>
          </div>
        </div>

        <ul className="mt-4 space-y-1.5">
          {sentiment.reasons.map((reason) => (
            <li key={reason} className="text-xs leading-relaxed text-foreground/90">
              • {reason}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  );
}
