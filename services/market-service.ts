import { getMockAssets, getMockAssetBySymbol, getMockMarketOverview } from "@/lib/mock/assets";
import { getMockCandles } from "@/lib/mock/candles";
import { mockDelay } from "@/lib/mock/delay";
import type { AssetQuote, Candle, MarketOverview } from "@/types";

export async function fetchAssets(): Promise<AssetQuote[]> {
  return mockDelay(getMockAssets());
}

export async function fetchAsset(symbol: string): Promise<AssetQuote | undefined> {
  return mockDelay(getMockAssetBySymbol(symbol));
}

export async function fetchMarketOverview(): Promise<MarketOverview> {
  return mockDelay(getMockMarketOverview());
}

export async function fetchCandles(symbol: string, basePrice: number): Promise<Candle[]> {
  return mockDelay(getMockCandles(symbol, 180, basePrice), 500);
}
