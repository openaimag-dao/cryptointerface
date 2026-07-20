import type { AssetQuote, MarketOverview } from "@/types";

// Fear & Greed / BTC dominance have no Binance data source — static until a
// dedicated macro data provider is wired up.
const STATIC_FEAR_GREED_INDEX = 62;
const STATIC_FEAR_GREED_LABEL = "Greed";
const STATIC_BTC_DOMINANCE = 54.2;

export function computeMarketOverview(assets: AssetQuote[]): MarketOverview {
  const totalVolume24h = assets.reduce((sum, asset) => sum + asset.volume24h, 0);
  const totalOpenInterest = assets.reduce((sum, asset) => sum + asset.openInterest, 0);
  const avgFundingRate = assets.length
    ? assets.reduce((sum, asset) => sum + asset.fundingRate, 0) / assets.length
    : 0;

  return {
    fearGreedIndex: STATIC_FEAR_GREED_INDEX,
    fearGreedLabel: STATIC_FEAR_GREED_LABEL,
    btcDominance: STATIC_BTC_DOMINANCE,
    avgFundingRate,
    totalOpenInterest,
    totalVolume24h,
  };
}
