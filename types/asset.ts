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
  volumeTrend: IndicatorReading;
  liquidityScore: IndicatorReading;
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

export type ExchangeDataStatus = "AVAILABLE" | "NOT_YET_IMPLEMENTED";

export interface ExchangeBreakdown {
  exchange: string;
  status: ExchangeDataStatus;
  openInterest: number | null;
  fundingRate: number | null;
  note: string;
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
  exchangeBreakdown: ExchangeBreakdown[];
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

export type ScenarioLabel = "BULLISH" | "NEUTRAL" | "BEARISH";
export type RiskLevel = "LOW" | "MODERATE" | "HIGH" | "EXTREME";
export type SignalOutcomeStatus = "WIN" | "LOSS" | "OPEN" | "NO_TRADE";

export interface Scenario {
  label: ScenarioLabel;
  probability: number;
  conditions: string[];
  targets: number[];
}

export interface RiskAnalysis {
  nearestSupport: number | null;
  nearestResistance: number | null;
  atr: number | null;
  atrRiskPct: number | null;
  volatilityScore: number;
  riskLevel: RiskLevel;
  maxRecommendedLeverage: number;
  drawdownRiskPct: number | null;
}

export interface AssetAnalysis {
  symbol: string;
  interval: string;
  direction: Direction;
  confidence: number;
  marketScore: number;
  entry: number | null;
  stop: number | null;
  tp1: number | null;
  tp2: number | null;
  tp3: number | null;
  riskReward: number | null;
  reasons: string[];
  scenarios: Scenario[];
  risk: RiskAnalysis;
}

export interface SignalOutcome {
  time: number;
  direction: Direction;
  score: number;
  confidence: number;
  entry: number | null;
  stop: number | null;
  tp1: number | null;
  outcome: SignalOutcomeStatus;
  pnlPercent: number | null;
}

export interface HistoryPoint {
  time: number;
  value: number;
}

export interface AssetHistory {
  symbol: string;
  interval: string;
  signals: SignalOutcome[];
  winRate: number | null;
  avgWinPnlPercent: number | null;
  avgLossPnlPercent: number | null;
  scoreHistory: HistoryPoint[];
  confidenceHistory: HistoryPoint[];
}

export interface CorrelationReading {
  reference: string;
  coefficient: number | null;
  dataPoints: number;
}

export type TimelineDataStatus = "OK" | "AWAITING_DATA";

export interface TimelineEntry {
  time: number;
  score: number;
  confidence: number;
  direction: Direction;
  changeSummary: string | null;
  reasons: string[] | null;
  strengthenedFactors: string[];
  weakenedFactors: string[];
  dataStatus: TimelineDataStatus;
}

export interface AssetTimeline {
  symbol: string;
  interval: string;
  entries: TimelineEntry[];
}
