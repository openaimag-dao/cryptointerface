"use client";

import { LIQUIDATION_TOTALS_24H } from "@/lib/mock/liquidations";
import { formatCompactNumber } from "@/lib/utils";
import { Card } from "@/components/ui/card";

export function LiquidationTotals() {
  const { longUsd, shortUsd } = LIQUIDATION_TOTALS_24H;
  const total = longUsd + shortUsd;
  const longPercent = (longUsd / total) * 100;

  return (
    <Card className="p-5">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          24h Liquidations
        </span>
        <span className="font-tabular text-sm font-semibold text-foreground">${formatCompactNumber(total)}</span>
      </div>

      <div className="mt-4 h-2.5 w-full overflow-hidden rounded-full bg-danger/20">
        <div className="h-full rounded-full bg-accent" style={{ width: `${longPercent}%` }} />
      </div>

      <div className="mt-3 flex items-center justify-between text-xs">
        <span className="flex items-center gap-1.5 text-accent">
          <span className="size-2 rounded-full bg-accent" />
          Longs ${formatCompactNumber(longUsd)}
        </span>
        <span className="flex items-center gap-1.5 text-danger">
          <span className="size-2 rounded-full bg-danger" />
          Shorts ${formatCompactNumber(shortUsd)}
        </span>
      </div>
    </Card>
  );
}
