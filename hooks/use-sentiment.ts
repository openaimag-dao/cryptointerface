import { useQuery } from "@tanstack/react-query";

import { fetchSentiment } from "@/services/sentiment-service";

export function useSentiment(symbol?: string, interval = "1h") {
  return useQuery({
    queryKey: ["sentiment", symbol ?? "default", interval],
    queryFn: () => fetchSentiment(symbol, interval),
    refetchInterval: 30_000,
  });
}
