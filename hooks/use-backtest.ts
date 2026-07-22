import { useMutation, useQuery } from "@tanstack/react-query";

import { fetchBacktestEquity, fetchBacktestHistory, fetchBacktestTrades, runBacktest } from "@/services/backtest-service";
import type { BacktestRunRequest } from "@/types";

export function useRunBacktest() {
  return useMutation({
    mutationFn: (request: BacktestRunRequest) => runBacktest(request),
  });
}

export function useBacktestTrades(runId: string | undefined) {
  return useQuery({
    queryKey: ["backtest-trades", runId],
    queryFn: () => fetchBacktestTrades(runId as string),
    enabled: Boolean(runId),
  });
}

export function useBacktestEquity(runId: string | undefined) {
  return useQuery({
    queryKey: ["backtest-equity", runId],
    queryFn: () => fetchBacktestEquity(runId as string),
    enabled: Boolean(runId),
  });
}

export function useBacktestHistory(symbol?: string) {
  return useQuery({
    queryKey: ["backtest-history", symbol],
    queryFn: () => fetchBacktestHistory(symbol),
  });
}
