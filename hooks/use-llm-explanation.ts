import { useQuery } from "@tanstack/react-query";

import { fetchLlmExplanation } from "@/services/llm-service";

export function useLlmExplanation(symbol: string, interval = "1h") {
  return useQuery({
    queryKey: ["llm-explanation", symbol, interval],
    queryFn: () => fetchLlmExplanation(symbol, interval),
    enabled: Boolean(symbol),
    refetchInterval: 60_000,
  });
}
