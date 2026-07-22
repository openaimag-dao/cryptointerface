import type { Direction } from "./market";

/**
 * Mirrors the backend's LLM Explanation Layer response shape (see
 * backend/app/schemas/llm.py). `direction`/`confidence` are always copied
 * straight from the deterministic AI Decision Engine — Claude only
 * produces `summary`/`keyDrivers`/`risks`/`opportunities`/`assetsAffected`.
 */
export interface LlmExplanation {
  symbol: string;
  interval: string;
  timestamp: number;
  direction: Direction;
  confidence: number;
  summary: string;
  keyDrivers: string[];
  risks: string[];
  opportunities: string[];
  assetsAffected: string[];
}
