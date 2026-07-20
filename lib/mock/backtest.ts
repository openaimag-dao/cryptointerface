import type { BacktestResult } from "@/types";

export function getMockBacktestResult(strategy: string, symbol: string, timeframe: string): BacktestResult {
  const points = 60;
  let equity = 10_000;
  const dayInSeconds = 60 * 60 * 24;
  const startTime = Math.floor(Date.now() / 1000) - points * dayInSeconds;
  const equityCurve = Array.from({ length: points }, (_, index) => {
    equity *= 1 + (Math.sin(index / 4) * 0.006 + 0.0045);
    return { time: startTime + index * dayInSeconds, value: Number(equity.toFixed(2)) };
  });

  return {
    id: `bt-${strategy}-${symbol}-${timeframe}`,
    strategy,
    symbol,
    timeframe,
    period: "Jan 2025 - Jul 2026",
    totalTrades: 214,
    winRate: 61.3,
    profitFactor: 1.84,
    totalReturnPercent: Number((((equity - 10_000) / 10_000) * 100).toFixed(1)),
    maxDrawdownPercent: -14.2,
    sharpeRatio: 1.62,
    equityCurve,
  };
}

export const BACKTEST_STRATEGIES = ["AI Momentum", "Mean Reversion", "Breakout Scalper", "Trend Following"];
