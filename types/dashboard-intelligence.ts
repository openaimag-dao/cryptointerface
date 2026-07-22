import type { LlmExplanation } from "./llm";
import type { Direction } from "./market";

/**
 * Mirrors backend/app/schemas/dashboard_intelligence.py. `overallScore` is
 * the AI Decision Engine's own Market Score (technical only); `sentimentScore`
 * is the broader Sentiment Engine blend across technical+macro+news+whales+
 * liquidations — two distinct numbers, not a duplicate.
 */
export interface DashboardIntelligence {
  symbol: string;
  interval: string;
  overallScore: number;
  direction: Direction;
  macroScore: number;
  newsScore: number;
  whaleScore: number;
  liquidationScore: number;
  sentimentScore: number;
  lastUpdated: string;
  aiExplanation: LlmExplanation | null;
}
