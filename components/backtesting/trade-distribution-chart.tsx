"use client";

import { BarChart } from "@/components/charts/bar-chart";
import { tradeDistribution } from "@/lib/backtest-charts";
import type { BacktestTrade } from "@/types";

export function TradeDistributionChart({ trades }: { trades: BacktestTrade[] }) {
  const data = tradeDistribution(trades);
  return <BarChart data={data} formatValue={(v) => `${v} trade(s)`} />;
}
