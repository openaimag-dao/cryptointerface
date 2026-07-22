import type { BacktestTrade } from "@/types";

/** One bar per calendar month a trade closed in, summing net PnL. */
export function monthlyReturns(trades: BacktestTrade[]): { label: string; value: number }[] {
  const byMonth = new Map<string, number>();
  for (const trade of trades) {
    const date = new Date(trade.exitTime * 1000);
    const label = `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, "0")}`;
    byMonth.set(label, (byMonth.get(label) ?? 0) + trade.pnl);
  }
  return Array.from(byMonth.entries())
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([label, value]) => ({ label, value }));
}

/** Trade PnL% bucketed into fixed-width ranges — the shape of the
 * strategy's return distribution, win and loss buckets side by side. */
export function tradeDistribution(trades: BacktestTrade[], bucketCount = 9): { label: string; value: number }[] {
  if (trades.length === 0) return [];

  const values = trades.map((t) => t.pnlPercent);
  const min = Math.min(...values);
  const max = Math.max(...values);
  if (min === max) {
    return [{ label: `${min.toFixed(1)}%`, value: trades.length }];
  }

  const bucketWidth = (max - min) / bucketCount;
  const counts = new Array(bucketCount).fill(0);
  for (const value of values) {
    const index = Math.min(bucketCount - 1, Math.floor((value - min) / bucketWidth));
    counts[index] += 1;
  }

  return counts.map((count, index) => {
    const rangeStart = min + index * bucketWidth;
    const rangeEnd = rangeStart + bucketWidth;
    return { label: `${rangeStart.toFixed(1)}/${rangeEnd.toFixed(1)}%`, value: count };
  });
}

/** Win count vs loss count — the two-bar "Win/Loss Histogram". */
export function winLossCounts(trades: BacktestTrade[]): { label: string; value: number }[] {
  const wins = trades.filter((t) => t.pnl > 0).length;
  const losses = trades.filter((t) => t.pnl < 0).length;
  return [
    { label: "Wins", value: wins },
    { label: "Losses", value: -losses },
  ];
}
