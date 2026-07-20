export type Direction = "LONG" | "SHORT" | "WAIT";

export type Sentiment = "BULLISH" | "BEARISH" | "NEUTRAL";

export interface Candle {
  time: number; // unix seconds
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface AssetQuote {
  symbol: string;
  name: string;
  price: number;
  changePercent24h: number;
  volume24h: number;
  fundingRate: number;
  openInterest: number;
  aiScore: number; // 0-100
  direction: Direction;
}

export interface MarketOverview {
  fearGreedIndex: number;
  fearGreedLabel: string;
  btcDominance: number;
  avgFundingRate: number;
  totalOpenInterest: number;
  totalVolume24h: number;
}
