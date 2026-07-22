"use client";

import { cn } from "@/lib/utils";
import { useAssetSentiment } from "@/hooks/use-asset";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { DirectionBadge } from "@/components/common/direction-badge";
import { RadarChart } from "@/components/charts/radar-chart";

interface SentimentTabProps {
  baseAsset: string;
  interval?: string;
}

const CATEGORY_LABELS: Record<string, string> = {
  technical: "Technical",
  macro: "Macro",
  liquidations: "Liquidations",
  news: "News",
  whales: "Whales",
};

export function SentimentTab({ baseAsset, interval = "1h" }: SentimentTabProps) {
  const { data: sentiment, isLoading } = useAssetSentiment(baseAsset, interval);

  if (isLoading || !sentiment) {
    return (
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Skeleton className="h-[320px] w-full rounded-xl" />
        <Skeleton className="h-[320px] w-full rounded-xl" />
      </div>
    );
  }

  const radar = sentiment.radar;

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle>Sentiment Radar</CardTitle>
          <DirectionBadge direction={sentiment.direction} size="sm" />
        </CardHeader>
        <CardContent className="flex flex-col items-center pt-0">
          <RadarChart
            axes={[
              { label: "News", value: radar.news },
              { label: "Social", value: radar.social },
              { label: "Whale", value: radar.whale },
              { label: "Technical", value: radar.technical },
              { label: "Macro", value: radar.macro },
              { label: "Market", value: radar.marketScore },
            ]}
          />
          <p className="mt-2 font-tabular text-sm text-muted-foreground">
            Overall score <span className="font-semibold text-foreground">{Math.round(sentiment.overallScore)}</span>
            {" · "}
            Confidence {Math.round(sentiment.confidence)}%
          </p>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle>Breakdown</CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          {Object.entries(sentiment.breakdown).map(([name, category]) => {
            const isStub = category.confidence === 0 && (name === "news" || name === "whales");
            return (
              <div key={name} className="border-b border-border-subtle py-2.5 last:border-b-0">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-foreground">{CATEGORY_LABELS[name] ?? name}</span>
                  <div className="flex items-center gap-2">
                    <span className="font-tabular text-xs text-muted-foreground">{Math.round(category.score)}/100</span>
                    <DirectionBadge direction={category.direction} size="sm" />
                  </div>
                </div>
                <p className={cn("mt-1 text-xs text-muted-foreground", isStub && "italic")}>
                  Confidence {Math.round(category.confidence)}%
                </p>
              </div>
            );
          })}
        </CardContent>
      </Card>
    </div>
  );
}
