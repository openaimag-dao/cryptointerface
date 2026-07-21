"use client";

import { BarChart } from "@/components/charts/bar-chart";
import { winLossCounts } from "@/lib/backtest-charts";
import type { BacktestTrade } from "@/types";

export function WinLossChart({ trades }: { trades: BacktestTrade[] }) {
  const data = winLossCounts(trades);
  return <BarChart data={data} formatValue={(v) => String(Math.abs(v))} />;
}
