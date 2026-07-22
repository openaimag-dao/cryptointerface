import { useQuery } from "@tanstack/react-query";

import {
  fetchAssetAnalysis,
  fetchAssetDerivatives,
  fetchAssetHistory,
  fetchAssetMacro,
  fetchAssetNews,
  fetchAssetOverview,
  fetchAssetSentiment,
  fetchAssetSummary,
  fetchAssetTechnical,
  fetchAssetWhales,
} from "@/services/asset-service";

export function useAssetSummary(symbol: string, interval = "1h") {
  return useQuery({
    queryKey: ["asset-summary", symbol, interval],
    queryFn: () => fetchAssetSummary(symbol, interval),
    enabled: Boolean(symbol),
    refetchInterval: 15_000,
  });
}

export function useAssetOverview(symbol: string, interval = "1h") {
  return useQuery({
    queryKey: ["asset-overview", symbol, interval],
    queryFn: () => fetchAssetOverview(symbol, interval),
    enabled: Boolean(symbol),
    refetchInterval: 30_000,
  });
}

export function useAssetTechnical(symbol: string, interval = "1h") {
  return useQuery({
    queryKey: ["asset-technical", symbol, interval],
    queryFn: () => fetchAssetTechnical(symbol, interval),
    enabled: Boolean(symbol),
    refetchInterval: 30_000,
  });
}

export function useAssetDerivatives(symbol: string) {
  return useQuery({
    queryKey: ["asset-derivatives", symbol],
    queryFn: () => fetchAssetDerivatives(symbol),
    enabled: Boolean(symbol),
    refetchInterval: 30_000,
  });
}

export function useAssetWhales(symbol: string) {
  return useQuery({
    queryKey: ["asset-whales", symbol],
    queryFn: () => fetchAssetWhales(symbol),
    enabled: Boolean(symbol),
    refetchInterval: 30_000,
  });
}

export function useAssetNews(symbol: string) {
  return useQuery({
    queryKey: ["asset-news", symbol],
    queryFn: () => fetchAssetNews(symbol),
    enabled: Boolean(symbol),
    refetchInterval: 60_000,
  });
}

export function useAssetMacro(symbol: string) {
  return useQuery({
    queryKey: ["asset-macro", symbol],
    queryFn: () => fetchAssetMacro(symbol),
    enabled: Boolean(symbol),
    refetchInterval: 60_000,
  });
}

export function useAssetSentiment(symbol: string, interval = "1h") {
  return useQuery({
    queryKey: ["asset-sentiment", symbol, interval],
    queryFn: () => fetchAssetSentiment(symbol, interval),
    enabled: Boolean(symbol),
    refetchInterval: 30_000,
  });
}

export function useAssetAnalysis(symbol: string, interval = "1h") {
  return useQuery({
    queryKey: ["asset-analysis", symbol, interval],
    queryFn: () => fetchAssetAnalysis(symbol, interval),
    enabled: Boolean(symbol),
    refetchInterval: 30_000,
  });
}

export function useAssetHistory(symbol: string, interval = "1h") {
  return useQuery({
    queryKey: ["asset-history", symbol, interval],
    queryFn: () => fetchAssetHistory(symbol, interval),
    enabled: Boolean(symbol),
    refetchInterval: 60_000,
  });
}
