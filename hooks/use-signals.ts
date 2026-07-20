import { useQuery } from "@tanstack/react-query";

import { fetchAiAnalysis, fetchSignals } from "@/services/signal-service";

export function useSignals() {
  return useQuery({
    queryKey: ["signals"],
    queryFn: fetchSignals,
    refetchInterval: 20_000,
  });
}

export function useAiAnalysis(symbol: string) {
  return useQuery({
    queryKey: ["ai-analysis", symbol],
    queryFn: () => fetchAiAnalysis(symbol),
    enabled: Boolean(symbol),
  });
}
