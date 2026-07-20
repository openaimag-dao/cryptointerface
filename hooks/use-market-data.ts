import { useQuery } from "@tanstack/react-query";

import { fetchAsset, fetchAssets, fetchCandles, fetchMarketOverview } from "@/services/market-service";

export function useAssets() {
  return useQuery({
    queryKey: ["assets"],
    queryFn: fetchAssets,
    refetchInterval: 15_000,
  });
}

export function useAsset(symbol: string) {
  return useQuery({
    queryKey: ["asset", symbol],
    queryFn: () => fetchAsset(symbol),
    refetchInterval: 15_000,
  });
}

export function useMarketOverview() {
  return useQuery({
    queryKey: ["market-overview"],
    queryFn: fetchMarketOverview,
    refetchInterval: 30_000,
  });
}

export function useCandles(symbol: string, basePrice: number) {
  return useQuery({
    queryKey: ["candles", symbol],
    queryFn: () => fetchCandles(symbol, basePrice),
    enabled: Boolean(symbol),
  });
}
