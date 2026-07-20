import type { Direction } from "./market";

export interface Position {
  id: string;
  symbol: string;
  direction: Direction;
  size: number;
  entryPrice: number;
  markPrice: number;
  pnl: number;
  pnlPercent: number;
  leverage: number;
  openedAt: string;
}

export interface TradeHistoryItem {
  id: string;
  symbol: string;
  direction: Direction;
  entryPrice: number;
  exitPrice: number;
  pnl: number;
  pnlPercent: number;
  openedAt: string;
  closedAt: string;
}

export interface PortfolioSummary {
  balance: number;
  equity: number;
  totalPnl: number;
  totalPnlPercent: number;
  winRate: number;
  totalTrades: number;
  openPositions: Position[];
  history: TradeHistoryItem[];
}
