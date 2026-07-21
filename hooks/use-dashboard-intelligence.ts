import { useQuery } from "@tanstack/react-query";

import { fetchDashboardIntelligence } from "@/services/dashboard-intelligence-service";

export function useDashboardIntelligence(symbol?: string, interval = "1h") {
  return useQuery({
    queryKey: ["dashboard-intelligence", symbol ?? "default", interval],
    queryFn: () => fetchDashboardIntelligence(symbol, interval),
    refetchInterval: 30_000,
  });
}
