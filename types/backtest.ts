/**
 * Mirrors the backend's Backtesting Engine response shapes (see
 * backend/app/schemas/backtest.py). The engine replays the unmodified
 * Sprint 3 AI Decision Engine bar by bar over historical candles — no
 * look-ahead, no simulated trade execution against Binance.
 */
export type TradeDirection = "LONG" | "SHORT";
export type ExitReason = "TP1" | "SL" | "END_OF_DATA";
export type BacktestRunStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";

export const BACKTEST_PERIOD_DAYS = [30, 90, 180, 365] as const;
export type BacktestPeriodDays = (typeof BACKTEST_PERIOD_DAYS)[number];

export interface BacktestRunRequest {
  symbol: string;
  timeframe: string;
  periodDays: BacktestPeriodDays;
  initialBalance?: number;
  commissionBps?: number;
  slippageBps?: number;
  riskPerTradePercent?: number;
}

export interface PerformanceMetrics {
  totalTrades: number;
  winningTrades: number;
  losingTrades: number;
  totalReturnPercent: number;
  netProfit: number;
  grossProfit: number;
  grossLoss: number;
  winRate: number;
  lossRate: number;
  avgWin: number;
  avgLoss: number;
  profitFactor: number;
  expectancy: number;
  avgTradeDurationSeconds: number;
}

export interface RiskMetrics {
  maxDrawdownPercent: number;
  maxDrawdownDurationSeconds: number;
  recoveryFactor: number;
  sharpeRatio: number;
  sortinoRatio: number;
  calmarRatio: number;
  avgRiskReward: number;
  finalBalance: number;
  peakBalance: number;
}

export interface BacktestTrade {
  id: string;
  symbol: string;
  direction: TradeDirection;
  entryTime: number;
  entryPrice: number;
  exitTime: number;
  exitPrice: number;
  quantity: number;
  pnl: number;
  pnlPercent: number;
  exitReason: ExitReason;
  durationSeconds: number;
  decisionScore: number;
  confidence: number;
  plannedRiskReward: number;
}

export interface EquityPoint {
  time: number;
  balance: number;
  drawdownPercent: number;
  cumulativePnl: number;
  tradeCount: number;
}

export interface BacktestRun {
  id: string;
  symbol: string;
  timeframe: string;
  periodDays: number;
  startTime: number;
  endTime: number;
  status: BacktestRunStatus;
  strategyVersionName: string;
  initialBalance: number;
  commissionBps: number;
  slippageBps: number;
  errorMessage: string | null;
  startedAt: number | null;
  completedAt: number | null;
  durationMs: number | null;
}

export interface BacktestMetrics {
  performance: PerformanceMetrics;
  risk: RiskMetrics;
}

export interface BacktestReport {
  run: BacktestRun;
  performance: PerformanceMetrics;
  risk: RiskMetrics;
}
