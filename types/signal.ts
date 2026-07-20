import type { Direction } from "./market";

export interface AiSignal {
  id: string;
  symbol: string;
  direction: Direction;
  confidence: number; // 0-100
  entry: number;
  stopLoss: number;
  takeProfit1: number;
  takeProfit2: number;
  takeProfit3: number;
  riskReward: number;
  reasons: string[];
  createdAt: string;
  timeframe: string;
}

