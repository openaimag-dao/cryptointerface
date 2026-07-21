import { useQuery } from "@tanstack/react-query";

import { fetchLiquidationHeatmap, fetchLiquidations, fetchLiquidationTotals } from "@/services/liquidation-service";

export function useLiquidations() {
  return useQuery({
    queryKey: ["liquidations"],
    queryFn: () => fetchLiquidations(),
    refetchInterval: 15_000,
  });
}

export function useLiquidationHeatmap() {
  return useQuery({
    queryKey: ["liquidation-heatmap"],
    queryFn: () => fetchLiquidationHeatmap(),
    refetchInterval: 30_000,
  });
}

export function useLiquidationTotals() {
  return useQuery({
    queryKey: ["liquidation-totals"],
    queryFn: fetchLiquidationTotals,
    refetchInterval: 30_000,
  });
}
