import { getMockBacktestResult } from "@/lib/mock/backtest";
import { mockDelay } from "@/lib/mock/delay";
import type { BacktestResult } from "@/types";

export async function runBacktest(strategy: string, symbol: string, timeframe: string): Promise<BacktestResult> {
  return mockDelay(getMockBacktestResult(strategy, symbol, timeframe), 900);
}
