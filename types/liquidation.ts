import type { Direction } from "./market";

export interface LiquidationEvent {
  id: string;
  symbol: string;
  side: Extract<Direction, "LONG" | "SHORT">;
  amountUsd: number;
  price: number;
  exchange: string;
  timestamp: string;
}

export interface LiquidationHeatmapCell {
  price: number;
  intensity: number; // 0-1
}

export interface LiquidationTotals {
  longUsd: number;
  shortUsd: number;
}
