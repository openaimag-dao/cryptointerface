"use client";

import { formatPercent } from "@/lib/utils";
import { StatTile } from "@/components/common/stat-tile";
import type { PerformanceMetrics, RiskMetrics } from "@/types";

export function BacktestSummaryCards({ performance, risk }: { performance: PerformanceMetrics; risk: RiskMetrics }) {
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-5">
      <StatTile
        label="Total Return"
        value={formatPercent(performance.totalReturnPercent)}
        tone={performance.totalReturnPercent >= 0 ? "positive" : "negative"}
      />
      <StatTile label="Win Rate" value={`${performance.winRate.toFixed(1)}%`} tone="positive" />
      <StatTile label="Profit Factor" value={performance.profitFactor.toFixed(2)} />
      <StatTile label="Sharpe Ratio" value={risk.sharpeRatio.toFixed(2)} />
      <StatTile label="Max Drawdown" value={formatPercent(-risk.maxDrawdownPercent)} tone="negative" />
    </div>
  );
}
