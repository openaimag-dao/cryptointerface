import { useQuery } from "@tanstack/react-query";

import { fetchWhaleTransactions } from "@/services/whale-service";

export function useWhaleTransactions() {
  return useQuery({
    queryKey: ["whale-transactions"],
    queryFn: fetchWhaleTransactions,
    refetchInterval: 20_000,
  });
}
