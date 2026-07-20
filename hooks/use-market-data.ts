import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";

import { computeMarketOverview } from "@/lib/market-overview";
import { fetchAsset, fetchAssets, fetchCandles } from "@/services/market-service";
import { useMarketStore } from "@/store/market-store";
import type { AssetQuote, TickerUpdateMessage } from "@/types";

function applyLiveTicker(asset: AssetQuote, ticker: TickerUpdateMessage | undefined): AssetQuote {
  if (!ticker) return asset;
  return {
    ...asset,
    price: ticker.price,
    changePercent24h: ticker.changePercent24h,
    volume24h: ticker.volume24h,
  };
}

export function useAssets() {
  const query = useQuery({
    queryKey: ["assets"],
    queryFn: fetchAssets,
    refetchInterval: 15_000,
  });
  const tickers = useMarketStore((state) => state.tickers);

  const data = useMemo(
    () => query.data?.map((asset) => applyLiveTicker(asset, tickers[asset.symbol])),
    [query.data, tickers],
  );

  return { ...query, data };
}

export function useAsset(symbol: string) {
  const query = useQuery({
    queryKey: ["asset", symbol],
    queryFn: () => fetchAsset(symbol),
    refetchInterval: 15_000,
  });
  const ticker = useMarketStore((state) => state.tickers[symbol]);

  const data = useMemo(() => (query.data ? applyLiveTicker(query.data, ticker) : query.data), [query.data, ticker]);

  return { ...query, data };
}

export function useMarketOverview() {
  const { data: assets, isLoading } = useAssets();
  return { data: assets ? computeMarketOverview(assets) : undefined, isLoading };
}

export function useCandles(symbol: string, interval: string) {
  return useQuery({
    queryKey: ["candles", symbol, interval],
    queryFn: () => fetchCandles(symbol, interval),
    enabled: Boolean(symbol),
  });
}
