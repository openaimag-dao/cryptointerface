"use client";

import { cn } from "@/lib/utils";
import { useAssetCorrelation } from "@/hooks/use-asset";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface CorrelationPanelProps {
  baseAsset: string;
  interval?: string;
}

export function CorrelationPanel({ baseAsset, interval = "1h" }: CorrelationPanelProps) {
  const { data: readings, isLoading } = useAssetCorrelation(baseAsset, interval);

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle>Correlation</CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        {isLoading || !readings ? (
          <div className="space-y-3">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-8 w-full" />
            ))}
          </div>
        ) : (
          <div className="space-y-2">
            {readings.map((reading) => (
              <div key={reading.reference} className="flex items-center justify-between gap-3">
                <span className="w-20 shrink-0 text-sm font-medium text-foreground">{reading.reference}</span>
                {reading.coefficient === null ? (
                  <span className="flex-1 text-right text-xs italic text-muted-foreground">
                    Insufficient data yet ({reading.dataPoints} points)
                  </span>
                ) : (
                  <>
                    <div className="relative h-1.5 flex-1 overflow-hidden rounded-full bg-white/[0.06]">
                      <div
                        className={cn(
                          "absolute top-0 h-full rounded-full",
                          reading.coefficient >= 0 ? "left-1/2 bg-accent" : "right-1/2 bg-danger",
                        )}
                        style={{ width: `${Math.abs(reading.coefficient) * 50}%` }}
                      />
                      <div className="absolute left-1/2 top-0 h-full w-px bg-white/20" />
                    </div>
                    <span className="w-14 shrink-0 text-right font-tabular text-xs text-foreground">
                      {reading.coefficient.toFixed(2)}
                    </span>
                  </>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
