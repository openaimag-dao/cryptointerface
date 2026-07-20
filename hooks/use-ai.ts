import { useQuery } from "@tanstack/react-query";

import { fetchAiDecision } from "@/services/ai-service";

export function useAiDecision(symbol: string, interval = "1h") {
  return useQuery({
    queryKey: ["ai-decision", symbol, interval],
    queryFn: () => fetchAiDecision(symbol, interval),
    enabled: Boolean(symbol),
    refetchInterval: 30_000,
  });
}
