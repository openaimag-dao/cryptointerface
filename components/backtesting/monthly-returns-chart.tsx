"use client";

import { BarChart } from "@/components/charts/bar-chart";
import { monthlyReturns } from "@/lib/backtest-charts";
import type { BacktestTrade } from "@/types";

export function MonthlyReturnsChart({ trades }: { trades: BacktestTrade[] }) {
  const data = monthlyReturns(trades);
  return <BarChart data={data} formatValue={(v) => `$${v.toFixed(2)}`} />;
}
