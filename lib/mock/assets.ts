import type { AssetQuote, Direction, MarketOverview } from "@/types";

interface AssetSeed {
  symbol: string;
  name: string;
  price: number;
}

const ASSET_SEEDS: AssetSeed[] = [
  { symbol: "BTCUSDT", name: "Bitcoin", price: 64280.5 },
  { symbol: "ETHUSDT", name: "Ethereum", price: 3412.8 },
  { symbol: "SOLUSDT", name: "Solana", price: 172.34 },
  { symbol: "LINKUSDT", name: "Chainlink", price: 18.62 },
  { symbol: "BNBUSDT", name: "BNB", price: 592.1 },
  { symbol: "XRPUSDT", name: "XRP", price: 0.612 },
  { symbol: "AVAXUSDT", name: "Avalanche", price: 38.47 },
  { symbol: "DOGEUSDT", name: "Dogecoin", price: 0.1523 },
  { symbol: "ADAUSDT", name: "Cardano", price: 0.478 },
  { symbol: "TONUSDT", name: "Toncoin", price: 6.94 },
];

function hashSeed(symbol: string): number {
  let hash = 0;
  for (let i = 0; i < symbol.length; i += 1) {
    hash = (hash << 5) - hash + symbol.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

function directionFromScore(score: number): Direction {
  if (score >= 65) return "LONG";
  if (score <= 35) return "SHORT";
  return "WAIT";
}

// Keeps the headline watchlist cards in sync with the curated AI Signals mock data.
const AI_SCORE_OVERRIDES: Record<string, { aiScore: number; direction: Direction }> = {
  BTCUSDT: { aiScore: 76, direction: "LONG" },
  ETHUSDT: { aiScore: 54, direction: "WAIT" },
  SOLUSDT: { aiScore: 88, direction: "LONG" },
  LINKUSDT: { aiScore: 29, direction: "SHORT" },
};

export function getMockAssets(): AssetQuote[] {
  return ASSET_SEEDS.map((seed) => {
    const seedHash = hashSeed(seed.symbol);
    const changePercent24h = ((seedHash % 900) - 450) / 40;
    const override = AI_SCORE_OVERRIDES[seed.symbol];
    const aiScore = override?.aiScore ?? 30 + (seedHash % 65);
    const volume24h = 80_000_000 + (seedHash % 40) * 32_000_000;
    const fundingRate = ((seedHash % 40) - 20) / 1000;
    const openInterest = 200_000_000 + (seedHash % 50) * 18_000_000;

    return {
      symbol: seed.symbol,
      name: seed.name,
      price: seed.price,
      changePercent24h,
      volume24h,
      fundingRate,
      openInterest,
      aiScore,
      direction: override?.direction ?? directionFromScore(aiScore),
    };
  });
}

export function getMockAssetBySymbol(symbol: string): AssetQuote | undefined {
  return getMockAssets().find((asset) => asset.symbol === symbol);
}

export function getMockMarketOverview(): MarketOverview {
  return {
    fearGreedIndex: 62,
    fearGreedLabel: "Greed",
    btcDominance: 54.2,
    avgFundingRate: 0.0086,
    totalOpenInterest: 38_400_000_000,
    totalVolume24h: 96_200_000_000,
  };
}

export const WATCHLIST_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "LINKUSDT"];
