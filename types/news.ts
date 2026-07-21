import type { Sentiment } from "./market";

/**
 * Mirrors the backend's News Engine response shape (see
 * backend/app/schemas/news.py). `symbols`/`impactScore`/`sentiment`/
 * `category` are all computed by a deterministic keyword classifier at
 * ingest time (app/intelligence/news/classifier.py) — no LLM call per
 * article.
 */
export interface NewsItem {
  id: string;
  source: string;
  title: string;
  summary: string;
  publishedAt: string;
  language: string;
  symbols: string[];
  url: string;
  impactScore: number;
  sentiment: Sentiment;
  category: string;
}
