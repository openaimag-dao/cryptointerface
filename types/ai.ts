import type { Direction } from "./market";

/**
 * Mirrors the backend's deterministic AI Decision Engine response shape
 * (see backend/app/schemas/ai.py). No mock data — this is the real
 * `/api/ai/decision/{symbol}` payload.
 */
export interface AiFactorScore {
  name: string;
  score: number;
  direction: Direction;
  strength: number;
  reasons: string[];
  details: Record<string, number | string | boolean>;
}

export interface AiRiskPlan {
  direction: Direction;
  entry: number;
  stop: number;
  tp1: number;
  tp2: number;
  tp3: number;
  riskPerUnit: number;
  riskRewardTp1: number;
  riskRewardTp2: number;
  riskRewardTp3: number;
}

export interface AiDecision {
  symbol: string;
  interval: string;
  timestamp: number;
  marketScore: number;
  confidence: number;
  direction: Direction;
  reasons: string[];
  factors: Record<string, AiFactorScore>;
  risk: AiRiskPlan | null;
}
