"use client";

import { useState } from "react";

import { WATCHLIST_SYMBOLS, getMockAssetBySymbol } from "@/lib/mock/assets";
import { formatCurrency, formatPercent } from "@/lib/utils";
import { useAsset, useCandles } from "@/hooks/use-market-data";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { CandlestickChart } from "@/components/charts/candlestick-chart";

const TIMEFRAMES = ["15m", "1H", "4H", "1D"];

interface PriceChartPanelProps {
  symbol: string;
  onSymbolChange: (symbol: string) => void;
}

export function PriceChartPanel({ symbol, onSymbolChange }: PriceChartPanelProps) {
  const [timeframe, setTimeframe] = useState("1H");

  const { data: asset } = useAsset(symbol);
  const basePrice = getMockAssetBySymbol(symbol)?.price ?? 64280;
  const { data: candles, isLoading } = useCandles(symbol, basePrice);

  const isUp = (asset?.changePercent24h ?? 0) >= 0;

  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="flex-row items-center justify-between gap-4 space-y-0 pb-4">
        <div className="flex items-center gap-4">
          <Tabs value={symbol} onValueChange={onSymbolChange}>
            <TabsList>
              {WATCHLIST_SYMBOLS.map((sym) => (
                <TabsTrigger key={sym} value={sym}>
                  {sym.replace("USDT", "")}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
          {asset ? (
            <div className="hidden items-baseline gap-2 sm:flex">
              <span className="font-tabular text-xl font-semibold text-foreground">
                {formatCurrency(asset.price)}
              </span>
              <span className={`font-tabular text-xs font-medium ${isUp ? "text-accent" : "text-danger"}`}>
                {formatPercent(asset.changePercent24h)}
              </span>
            </div>
          ) : null}
        </div>

        <Tabs value={timeframe} onValueChange={setTimeframe}>
          <TabsList>
            {TIMEFRAMES.map((tf) => (
              <TabsTrigger key={tf} value={tf}>
                {tf}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>
      </CardHeader>
      <CardContent className="flex-1 pt-0">
        {isLoading || !candles ? (
          <Skeleton className="h-[420px] w-full rounded-lg" />
        ) : (
          <CandlestickChart data={candles} height={420} />
        )}
      </CardContent>
    </Card>
  );
}
