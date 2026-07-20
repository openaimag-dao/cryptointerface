import { useQuery } from "@tanstack/react-query";

import { fetchSignals } from "@/services/signal-service";

export function useSignals() {
  return useQuery({
    queryKey: ["signals"],
    queryFn: fetchSignals,
    refetchInterval: 20_000,
  });
}
