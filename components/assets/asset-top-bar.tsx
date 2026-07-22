"use client";

import { Star } from "lucide-react";

import { cn, formatCompactNumber, formatCurrency, formatPercent } from "@/lib/utils";
import { useAssetSummary } from "@/hooks/use-asset";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { DirectionBadge } from "@/components/common/direction-badge";
import { AiScoreRing } from "@/components/common/ai-score-ring";

interface AssetTopBarProps {
  baseAsset: string;
}

function ChangeStat({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="flex flex-col items-start gap-0.5">
      <span className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</span>
      {value === null ? (
        <span className="text-xs text-muted-foreground">—</span>
      ) : (
        <span className={cn("font-tabular text-sm font-medium", value >= 0 ? "text-accent" : "text-danger")}>
          {formatPercent(value)}
        </span>
      )}
    </div>
  );
}

function PlainStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col items-start gap-0.5">
      <span className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</span>
      <span className="font-tabular text-sm font-medium text-foreground">{value}</span>
    </div>
  );
}

export function AssetTopBar({ baseAsset }: AssetTopBarProps) {
  const { data: summary, isLoading } = useAssetSummary(baseAsset);

  if (isLoading || !summary) {
    return (
      <Card className="p-5">
        <Skeleton className="h-16 w-full" />
      </Card>
    );
  }

  return (
    <Card className="p-5">
      <div className="flex flex-wrap items-center justify-between gap-6">
        <div className="flex items-center gap-4">
          <div className="flex size-11 items-center justify-center rounded-full border border-border-strong bg-white/[0.04] font-tabular text-sm font-semibold text-foreground">
            {summary.baseAsset.slice(0, 4)}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-semibold tracking-tight text-foreground">{summary.baseAsset}</h1>
              <DirectionBadge direction={summary.direction ?? "WAIT"} size="sm" />
            </div>
            <div className="flex items-baseline gap-2">
              <span className="font-tabular text-2xl font-semibold text-foreground">
                {formatCurrency(summary.price)}
              </span>
              <span
                className={cn(
                  "font-tabular text-xs font-medium",
                  summary.changePercent24h >= 0 ? "text-accent" : "text-danger",
                )}
              >
                {formatPercent(summary.changePercent24h)} 24h
              </span>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-x-6 gap-y-3">
          <ChangeStat label="7d" value={summary.changePercent7d} />
          <ChangeStat label="30d" value={summary.changePercent30d} />
          <PlainStat
            label="Market Cap"
            value={summary.marketCap !== null ? `$${formatCompactNumber(summary.marketCap)}` : "—"}
          />
          <PlainStat label="Volume 24h" value={`$${formatCompactNumber(summary.volume24h)}`} />
          <PlainStat
            label="Funding"
            value={summary.fundingRate !== null ? formatPercent(summary.fundingRate * 100) : "—"}
          />
          <PlainStat
            label="Open Interest"
            value={summary.openInterest !== null ? formatCompactNumber(summary.openInterest) : "—"}
          />
          <div className="flex flex-col items-start gap-0.5">
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground">AI Score</span>
            <AiScoreRing score={Math.round(summary.marketScore ?? 0)} size={36} strokeWidth={3} />
          </div>
          <PlainStat label="Confidence" value={summary.confidence !== null ? `${Math.round(summary.confidence)}%` : "—"} />
        </div>

        <Button variant="outline" size="sm" disabled className="gap-1.5" title="Watchlist is coming in a future update">
          <Star className="size-3.5" />
          Add to Watchlist
        </Button>
      </div>
    </Card>
  );
}
