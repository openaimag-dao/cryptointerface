import type { Direction } from "./market";
import type { SentimentCategory } from "./sentiment";
import type { WhaleTransaction } from "./whale";

/**
 * Mirrors the backend's Asset Intelligence Dashboard response shapes (see
 * backend/app/schemas/asset.py). Every `/api/assets/{symbol}/*` endpoint
 * aggregates the existing Data/AI/Intelligence Engines per symbol — see
 * backend/app/services/asset_service.py.
 */

export type IndicatorStatus =
  | "BULLISH"
  | "BEARISH"
  | "NEUTRAL"
  | "OVERBOUGHT"
  | "OVERSOLD"
  | "TRENDING"
  | "RANGING"
  | "TRANSITIONAL"
  | "HIGH"
  | "LOW"
  | "MODERATE";

export type SmartMoneyStatus = "BULLISH" | "BEARISH" | "NEUTRAL" | "NOT_YET_IMPLEMENTED";
export type BreakoutStatus = "BROKEN_ABOVE_RESISTANCE" | "BROKEN_BELOW_SUPPORT" | "INSIDE_RANGE";
export type TrendDirection = "UP" | "DOWN" | "NEUTRAL";
export type MacroInfluence = "HIGH" | "LOW";

export interface AssetSummary {
  symbol: string;
  baseAsset: string;
  price: number;
  changePercent24h: number;
  changePercent7d: number | null;
  changePercent30d: number | null;
  marketCap: number | null;
  volume24h: number;
  fundingRate: number | null;
  openInterest: number | null;
  marketScore: number | null;
  confidence: number | null;
  direction: Direction | null;
}

export interface IndicatorReading {
  name: string;
  value: string;
  status: IndicatorStatus;
  explanation: string;
}

export interface AssetOverview {
  trendStatus: Direction;
  volatilityStatus: Direction;
  atr: IndicatorReading;
  rsi: IndicatorReading;
  macd: IndicatorReading;
  emaAlignment: IndicatorReading;
  vwap: IndicatorReading;
}

export interface SmartMoneyConcept {
  name: string;
  status: SmartMoneyStatus;
  value: string | null;
  explanation: string;
}

export interface AssetTechnical {
  symbol: string;
  interval: string;
  indicators: IndicatorReading[];
  smartMoney: SmartMoneyConcept[];
  nearestSupport: number | null;
  nearestResistance: number | null;
  breakoutStatus: BreakoutStatus;
}

export interface FundingHistoryPoint {
  time: number;
  rate: number;
}

export interface LiquidationCluster {
  priceLow: number;
  priceHigh: number;
  totalUsd: number;
  eventCount: number;
}

export interface AssetDerivatives {
  symbol: string;
  fundingRate: number | null;
  fundingHistory: FundingHistoryPoint[];
  fundingTrend: TrendDirection;
  openInterest: number | null;
  openInterestValue: number | null;
  oiDeltaPercent: number | null;
  liquidationClusters: LiquidationCluster[];
}

export interface AssetWhales {
  symbol: string;
  asset: string | null;
  whaleScore: number;
  events: WhaleTransaction[];
  toExchangeUsd24h: number;
  fromExchangeUsd24h: number;
}

export interface MacroInfluenceReading {
  id: string;
  label: string;
  current: number | null;
  changePercent: number | null;
  trend: TrendDirection;
  influence: MacroInfluence;
}

export interface SentimentRadar {
  news: number;
  social: number | null;
  whale: number;
  technical: number;
  macro: number;
  marketScore: number;
}

export interface AssetSentiment {
  symbol: string;
  interval: string;
  timestamp: number;
  overallScore: number;
  confidence: number;
  direction: Direction;
  breakdown: Record<string, SentimentCategory>;
  reasons: string[];
  radar: SentimentRadar;
}
