export interface BacktestResult {
  id: string;
  strategy: string;
  symbol: string;
  timeframe: string;
  period: string;
  totalTrades: number;
  winRate: number;
  profitFactor: number;
  totalReturnPercent: number;
  maxDrawdownPercent: number;
  sharpeRatio: number;
  equityCurve: { time: number; value: number }[];
}
