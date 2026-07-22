import type { Direction } from "./market";

/**
 * Mirrors the backend's Sentiment Engine response shape (see
 * backend/app/schemas/sentiment.py / app/intelligence/sentiment/engine.py).
 * `breakdown`'s keys are "technical" | "macro" | "liquidations" | "news" |
 * "whales" — the last two are Sprint 4 stubs (neutral, zero confidence)
 * until real news/whale ingestion lands in a follow-up sprint.
 */
export interface SentimentCategory {
  score: number;
  direction: Direction;
  confidence: number;
  reasons: string[];
}

export interface SentimentSnapshot {
  symbol: string;
  interval: string;
  timestamp: number;
  overallScore: number;
  confidence: number;
  direction: Direction;
  breakdown: Record<string, SentimentCategory>;
  reasons: string[];
}
