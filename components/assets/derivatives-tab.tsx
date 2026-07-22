"use client";

import { cn, formatCompactNumber, formatPercent } from "@/lib/utils";
import { useAssetDerivatives } from "@/hooks/use-asset";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { BarChart } from "@/components/charts/bar-chart";
import { LineChart } from "@/components/charts/line-chart";
import type { ExchangeDataStatus, LiquidationCluster } from "@/types";

interface DerivativesTabProps {
  baseAsset: string;
}

const EXCHANGE_STATUS_CLASSNAME: Record<ExchangeDataStatus, string> = {
  AVAILABLE: "border-accent/30 bg-accent-dim text-accent",
  NOT_YET_IMPLEMENTED: "border-border-strong bg-white/[0.02] text-muted-foreground opacity-60",
};

function ExchangeStatusBadge({ status }: { status: ExchangeDataStatus }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
        EXCHANGE_STATUS_CLASSNAME[status],
      )}
    >
      {status === "AVAILABLE" ? "Live" : "Not yet implemented"}
    </span>
  );
}

function LiquidationHeatmap({ clusters }: { clusters: LiquidationCluster[] }) {
  if (clusters.length === 0) {
    return <p className="py-10 text-center text-xs text-muted-foreground">No recent liquidations to map.</p>;
  }

  const maxUsd = Math.max(...clusters.map((c) => c.totalUsd));

  return (
    <div className="flex h-[220px] items-end gap-1" role="img" aria-label="Liquidation heat map by price level">
      {clusters.map((cluster, i) => {
        const intensity = maxUsd > 0 ? cluster.totalUsd / maxUsd : 0;
        return (
          <div
            key={i}
            className="flex flex-1 flex-col items-center justify-end gap-1"
            title={`${formatCompactNumber(cluster.priceLow)}–${formatCompactNumber(cluster.priceHigh)}: $${formatCompactNumber(cluster.totalUsd)} across ${cluster.eventCount} events`}
          >
            <div
              className="w-full rounded-sm"
              style={{
                height: `${Math.max(intensity * 100, 4)}%`,
                backgroundColor: `rgba(255, 87, 87, ${0.15 + intensity * 0.7})`,
              }}
            />
            <span className="text-[9px] text-muted-foreground">{formatCompactNumber(cluster.priceLow)}</span>
          </div>
        );
      })}
    </div>
  );
}

function Stat({ label, value, tone }: { label: string; value: string; tone?: "positive" | "negative" }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</span>
      <span
        className={cn(
          "font-tabular text-sm font-medium",
          tone === "positive" && "text-accent",
          tone === "negative" && "text-danger",
          !tone && "text-foreground",
        )}
      >
        {value}
      </span>
    </div>
  );
}

export function DerivativesTab({ baseAsset }: DerivativesTabProps) {
  const { data: derivatives, isLoading } = useAssetDerivatives(baseAsset);

  if (isLoading || !derivatives) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-32 w-full rounded-xl" />
        <Skeleton className="h-64 w-full rounded-xl" />
      </div>
    );
  }

  const fundingSeries = derivatives.fundingHistory.map((point) => ({ time: point.time, value: point.rate * 100 }));
  const clusterData = derivatives.liquidationClusters.map((cluster) => ({
    label: `${formatCompactNumber(cluster.priceLow)}`,
    value: cluster.totalUsd,
  }));

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle>Funding &amp; Open Interest</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-4 pt-0 sm:grid-cols-4">
          <Stat
            label="Funding Rate"
            value={derivatives.fundingRate !== null ? formatPercent(derivatives.fundingRate * 100) : "—"}
            tone={derivatives.fundingRate !== null ? (derivatives.fundingRate >= 0 ? "positive" : "negative") : undefined}
          />
          <Stat label="Funding Trend" value={derivatives.fundingTrend} />
          <Stat
            label="Open Interest"
            value={derivatives.openInterest !== null ? formatCompactNumber(derivatives.openInterest) : "—"}
          />
          <Stat
            label="OI Delta"
            value={derivatives.oiDeltaPercent !== null ? formatPercent(derivatives.oiDeltaPercent) : "—"}
            tone={derivatives.oiDeltaPercent !== null ? (derivatives.oiDeltaPercent >= 0 ? "positive" : "negative") : undefined}
          />
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle>Funding History</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            {fundingSeries.length > 1 ? (
              <LineChart data={fundingSeries} height={220} color="#38bdf8" />
            ) : (
              <p className="py-10 text-center text-xs text-muted-foreground">Not enough funding history yet.</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle>Liquidation Clusters</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <BarChart data={clusterData} height={220} formatValue={(v) => `$${formatCompactNumber(v)}`} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle>Liquidation Heat Map</CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          <LiquidationHeatmap clusters={derivatives.liquidationClusters} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle>Exchange Breakdown</CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          {derivatives.exchangeBreakdown.map((entry) => (
            <div
              key={entry.exchange}
              className="flex items-center justify-between gap-3 border-b border-border-subtle py-2.5 last:border-b-0"
            >
              <div className="min-w-0">
                <p className="text-sm font-medium text-foreground">{entry.exchange}</p>
                <p className="truncate text-xs text-muted-foreground">{entry.note}</p>
              </div>
              <div className="flex shrink-0 items-center gap-3">
                <span className="font-tabular text-xs text-muted-foreground">
                  {entry.openInterest !== null ? formatCompactNumber(entry.openInterest) : "—"}
                </span>
                <ExchangeStatusBadge status={entry.status} />
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
