import { apiFetch } from "@/lib/api-client";
import { getAiOverlay } from "@/lib/mock/ai-overlay";
import type { AssetQuote, Candle, MarketAsset } from "@/types";

function toAssetQuote(asset: MarketAsset): AssetQuote {
  const overlay = getAiOverlay(asset.symbol);
  return {
    symbol: asset.symbol,
    name: overlay.name,
    price: asset.price,
    changePercent24h: asset.changePercent24h,
    volume24h: asset.volume24h,
    fundingRate: asset.fundingRate ?? 0,
    openInterest: asset.openInterest ?? 0,
    aiScore: overlay.aiScore,
    direction: overlay.direction,
  };
}

export async function fetchAssets(): Promise<AssetQuote[]> {
  const assets = await apiFetch<MarketAsset[]>("/api/market");
  return assets.map(toAssetQuote);
}

export async function fetchAsset(symbol: string): Promise<AssetQuote | undefined> {
  try {
    const asset = await apiFetch<MarketAsset>(`/api/market/${symbol}`);
    return toAssetQuote(asset);
  } catch {
    return undefined;
  }
}

export async function fetchCandles(symbol: string, interval: string, limit = 500): Promise<Candle[]> {
  return apiFetch<Candle[]>(`/api/candles/${symbol}?interval=${interval}&limit=${limit}`);
}
