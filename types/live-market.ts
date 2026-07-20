import type { Candle } from "./market";

export interface MarketAsset {
  symbol: string;
  price: number;
  changePercent24h: number;
  high24h: number;
  low24h: number;
  volume24h: number;
  quoteVolume24h: number;
  fundingRate: number | null;
  openInterest: number | null;
  updatedAt: string;
}

export interface EmaValues {
  ema20: number | null;
  ema50: number | null;
  ema100: number | null;
  ema200: number | null;
}

export interface MacdValues {
  macd: number | null;
  signal: number | null;
  histogram: number | null;
}

export interface BollingerBandsValues {
  upper: number | null;
  middle: number | null;
  lower: number | null;
}

export interface StochRsiValues {
  k: number | null;
  d: number | null;
}

export interface PivotLevels {
  pivot: number | null;
  r1: number | null;
  r2: number | null;
  r3: number | null;
  s1: number | null;
  s2: number | null;
  s3: number | null;
}

export interface IndicatorSnapshot {
  symbol: string;
  interval: string;
  time: number;
  ema: EmaValues;
  rsi14: number | null;
  macd: MacdValues;
  atr14: number | null;
  bollingerBands: BollingerBandsValues;
  vwap: number | null;
  adx14: number | null;
  obv: number | null;
  stochRsi: StochRsiValues;
  pivot: PivotLevels;
}

export interface FundingRateData {
  symbol: string;
  fundingRate: number;
  markPrice: number;
  fundingTime: number;
  nextFundingTime: number | null;
}

export interface OpenInterestData {
  symbol: string;
  openInterest: number;
  openInterestValue: number;
  timestamp: number;
}

export interface SymbolFeedStatus {
  symbol: string;
  lastTradeAt: string | null;
  lastKlineAt: string | null;
  lastFundingAt: string | null;
}

export type BinanceWsState = "connected" | "connecting" | "disconnected";

export interface EngineStatus {
  environment: string;
  databaseConnected: boolean;
  redisConnected: boolean;
  binanceWsState: BinanceWsState;
  trackedSymbols: string[];
  trackedTimeframes: string[];
  symbolFeeds: SymbolFeedStatus[];
  connectedFrontendClients: number;
  uptimeSeconds: number;
}

export interface CandleUpdateMessage {
  symbol: string;
  interval: string;
  candle: Candle;
  isClosed: boolean;
}

export interface TickerUpdateMessage {
  symbol: string;
  price: number;
  changePercent24h: number;
  high24h: number;
  low24h: number;
  volume24h: number;
  quoteVolume24h: number;
}

export interface TradeUpdateMessage {
  symbol: string;
  price: number;
  quantity: number;
  tradeTime: number;
  isBuyerMaker: boolean;
}

export type WsEnvelope =
  | { channel: "candle"; data: CandleUpdateMessage }
  | { channel: "ticker"; data: TickerUpdateMessage }
  | { channel: "indicators"; data: IndicatorSnapshot }
  | { channel: "funding"; data: FundingRateData }
  | { channel: "trade"; data: TradeUpdateMessage };
