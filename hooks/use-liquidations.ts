import { useQuery } from "@tanstack/react-query";

import { fetchLiquidationHeatmap, fetchLiquidations } from "@/services/liquidation-service";

export function useLiquidations() {
  return useQuery({
    queryKey: ["liquidations"],
    queryFn: fetchLiquidations,
    refetchInterval: 15_000,
  });
}

export function useLiquidationHeatmap() {
  return useQuery({
    queryKey: ["liquidation-heatmap"],
    queryFn: fetchLiquidationHeatmap,
    refetchInterval: 30_000,
  });
}
