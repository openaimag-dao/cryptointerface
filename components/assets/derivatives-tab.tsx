"use client";

import { cn, formatCompactNumber, formatPercent } from "@/lib/utils";
import { useAssetDerivatives } from "@/hooks/use-asset";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { BarChart } from "@/components/charts/bar-chart";
import { LineChart } from "@/components/charts/line-chart";

interface DerivativesTabProps {
  baseAsset: string;
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
    </div>
  );
}
