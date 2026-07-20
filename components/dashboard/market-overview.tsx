"use client";

import { Activity, BarChart3, Gauge, PieChart, Percent } from "lucide-react";

import { formatCompactNumber, formatPercent } from "@/lib/utils";
import { useMarketOverview } from "@/hooks/use-market-data";
import { StatTile } from "@/components/common/stat-tile";
import { Skeleton } from "@/components/ui/skeleton";

export function MarketOverview() {
  const { data, isLoading } = useMarketOverview();

  if (isLoading || !data) {
    return (
      <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-5">
        {Array.from({ length: 5 }).map((_, index) => (
          <Skeleton key={index} className="h-[90px] rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-5">
      <StatTile
        label="Fear & Greed"
        value={String(data.fearGreedIndex)}
        hint={data.fearGreedLabel}
        icon={Gauge}
        tone={data.fearGreedIndex >= 55 ? "positive" : data.fearGreedIndex <= 35 ? "negative" : "default"}
      />
      <StatTile label="BTC Dominance" value={`${data.btcDominance.toFixed(1)}%`} icon={PieChart} />
      <StatTile
        label="Avg. Funding"
        value={formatPercent(data.avgFundingRate * 100)}
        icon={Percent}
        tone={data.avgFundingRate >= 0 ? "positive" : "negative"}
      />
      <StatTile label="Open Interest" value={`$${formatCompactNumber(data.totalOpenInterest)}`} icon={Activity} />
      <StatTile label="24h Volume" value={`$${formatCompactNumber(data.totalVolume24h)}`} icon={BarChart3} />
    </div>
  );
}
