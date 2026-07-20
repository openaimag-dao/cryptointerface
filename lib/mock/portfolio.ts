import type { PortfolioSummary, Position, TradeHistoryItem } from "@/types";

const OPEN_POSITIONS: Position[] = [
  {
    id: "pos-1",
    symbol: "BTCUSDT",
    direction: "LONG",
    size: 0.42,
    entryPrice: 61200,
    markPrice: 64280.5,
    pnl: 1293.8,
    pnlPercent: 5.03,
    leverage: 5,
    openedAt: new Date(Date.now() - 1000 * 60 * 60 * 26).toISOString(),
  },
  {
    id: "pos-2",
    symbol: "SOLUSDT",
    direction: "LONG",
    size: 65,
    entryPrice: 158.2,
    markPrice: 172.34,
    pnl: 918.1,
    pnlPercent: 8.94,
    leverage: 3,
    openedAt: new Date(Date.now() - 1000 * 60 * 60 * 9).toISOString(),
  },
  {
    id: "pos-3",
    symbol: "LINKUSDT",
    direction: "SHORT",
    size: 420,
    entryPrice: 19.4,
    markPrice: 18.62,
    pnl: 327.6,
    pnlPercent: 4.02,
    leverage: 4,
    openedAt: new Date(Date.now() - 1000 * 60 * 60 * 3).toISOString(),
  },
];

const TRADE_HISTORY: TradeHistoryItem[] = [
  {
    id: "trade-1",
    symbol: "ETHUSDT",
    direction: "LONG",
    entryPrice: 3180,
    exitPrice: 3412.8,
    pnl: 698.4,
    pnlPercent: 7.32,
    openedAt: new Date(Date.now() - 1000 * 60 * 60 * 96).toISOString(),
    closedAt: new Date(Date.now() - 1000 * 60 * 60 * 48).toISOString(),
  },
  {
    id: "trade-2",
    symbol: "AVAXUSDT",
    direction: "SHORT",
    entryPrice: 41.2,
    exitPrice: 38.47,
    pnl: 212.5,
    pnlPercent: 6.62,
    openedAt: new Date(Date.now() - 1000 * 60 * 60 * 72).toISOString(),
    closedAt: new Date(Date.now() - 1000 * 60 * 60 * 60).toISOString(),
  },
  {
    id: "trade-3",
    symbol: "DOGEUSDT",
    direction: "LONG",
    entryPrice: 0.162,
    exitPrice: 0.1523,
    pnl: -184.2,
    pnlPercent: -6.0,
    openedAt: new Date(Date.now() - 1000 * 60 * 60 * 130).toISOString(),
    closedAt: new Date(Date.now() - 1000 * 60 * 60 * 118).toISOString(),
  },
  {
    id: "trade-4",
    symbol: "BNBUSDT",
    direction: "LONG",
    entryPrice: 560.1,
    exitPrice: 592.1,
    pnl: 384.0,
    pnlPercent: 5.71,
    openedAt: new Date(Date.now() - 1000 * 60 * 60 * 200).toISOString(),
    closedAt: new Date(Date.now() - 1000 * 60 * 60 * 188).toISOString(),
  },
];

export function getMockPortfolio(): PortfolioSummary {
  const totalPnl = OPEN_POSITIONS.reduce((sum, position) => sum + position.pnl, 0);
  const balance = 42_500;

  return {
    balance,
    equity: balance + totalPnl,
    totalPnl,
    totalPnlPercent: Number(((totalPnl / balance) * 100).toFixed(2)),
    winRate: 68.4,
    totalTrades: 156,
    openPositions: OPEN_POSITIONS,
    history: TRADE_HISTORY,
  };
}
