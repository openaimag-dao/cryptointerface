"use client";

import { useState } from "react";

import { CHART_TIMEFRAMES, type ChartTimeframe } from "@/lib/constants";
import { useCandles } from "@/hooks/use-market-data";
import { useAssetOverview } from "@/hooks/use-asset";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { CandlestickChart } from "@/components/charts/candlestick-chart";
import { IndicatorStatusBadge } from "@/components/assets/indicator-status-badge";
import type { Direction, IndicatorReading } from "@/types";

interface OverviewTabProps {
  symbol: string; // trading pair, e.g. BTCUSDT
  baseAsset: string;
}

function directionStatus(direction: Direction): "BULLISH" | "BEARISH" | "NEUTRAL" {
  if (direction === "LONG") return "BULLISH";
  if (direction === "SHORT") return "BEARISH";
  return "NEUTRAL";
}

function SnapshotRow({ reading }: { reading: IndicatorReading }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-border-subtle py-2.5 last:border-b-0">
      <div className="min-w-0">
        <p className="text-sm font-medium text-foreground">{reading.name}</p>
        <p className="truncate text-xs text-muted-foreground">{reading.explanation}</p>
      </div>
      <div className="flex shrink-0 items-center gap-2">
        <span className="font-tabular text-xs text-muted-foreground">{reading.value}</span>
        <IndicatorStatusBadge status={reading.status} />
      </div>
    </div>
  );
}

export function OverviewTab({ symbol, baseAsset }: OverviewTabProps) {
  const [timeframe, setTimeframe] = useState<ChartTimeframe>("1h");
  const { data: candles, isLoading: candlesLoading } = useCandles(symbol, timeframe);
  const { data: overview, isLoading: overviewLoading } = useAssetOverview(baseAsset, timeframe);

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
      <Card className="flex flex-col lg:col-span-2">
        <CardHeader className="flex-row items-center justify-between space-y-0 pb-4">
          <CardTitle>Price Chart</CardTitle>
          <Tabs value={timeframe} onValueChange={(value) => setTimeframe(value as ChartTimeframe)}>
            <TabsList>
              {CHART_TIMEFRAMES.map((tf) => (
                <TabsTrigger key={tf} value={tf}>
                  {tf.toUpperCase()}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
        </CardHeader>
        <CardContent className="flex-1 pt-0">
          {candlesLoading || !candles ? (
            <Skeleton className="h-[420px] w-full rounded-lg" />
          ) : (
            <CandlestickChart data={candles} height={420} symbol={symbol} interval={timeframe} />
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle>Market Snapshot</CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          {overviewLoading || !overview ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : (
            <div>
              <div className="flex items-center justify-between border-b border-border-subtle py-2.5">
                <span className="text-sm font-medium text-foreground">Trend</span>
                <IndicatorStatusBadge status={directionStatus(overview.trendStatus)} />
              </div>
              <div className="flex items-center justify-between border-b border-border-subtle py-2.5">
                <span className="text-sm font-medium text-foreground">Volatility</span>
                <IndicatorStatusBadge status={directionStatus(overview.volatilityStatus)} />
              </div>
              <SnapshotRow reading={overview.atr} />
              <SnapshotRow reading={overview.rsi} />
              <SnapshotRow reading={overview.macd} />
              <SnapshotRow reading={overview.emaAlignment} />
              <SnapshotRow reading={overview.vwap} />
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
