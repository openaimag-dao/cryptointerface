import { useMutation } from "@tanstack/react-query";

import { runBacktest } from "@/services/backtest-service";

export function useRunBacktest() {
  return useMutation({
    mutationFn: ({ strategy, symbol, timeframe }: { strategy: string; symbol: string; timeframe: string }) =>
      runBacktest(strategy, symbol, timeframe),
  });
}
