import type { Sentiment } from "./market";

/**
 * Mirrors the backend's News Engine response shape (see
 * backend/app/schemas/news.py). `symbols`/`impactScore`/`sentiment`/
 * `category` are all computed by a deterministic keyword classifier at
 * ingest time (app/intelligence/news/classifier.py) — no LLM call per
 * article.
 */
export type PortalTopic = "CRYPTO" | "AI" | "BLOCKCHAIN" | "INNOVATION";

/**
 * One AI-extracted named thing (company/person/cryptocurrency/protocol/
 * country/technology) an article mentions — see backend/app/models/
 * entity.py. `slug` links to its /tag/{slug} archive page. Absent/empty
 * until the AI News Processing pipeline reaches an article.
 */
export interface EntityTag {
  name: string;
  slug: string;
  entityType: "COMPANY" | "PERSON" | "CRYPTOCURRENCY" | "PROTOCOL" | "COUNTRY" | "TECHNOLOGY";
}

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
  portalTopic: PortalTopic | null;
  aiSummary: string | null;
  imageUrl: string | null;
  entities: EntityTag[];
}

export interface PortalNewsPage {
  items: NewsItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface EntityNewsPage {
  entity: EntityTag;
  items: NewsItem[];
  total: number;
  limit: number;
  offset: number;
}

/**
 * Generated on a schedule by the backend from real ingested articles for
 * one topic (see backend/app/intelligence/llm/news_digest.py) — narration
 * only, every claim is grounded in the articles it was given.
 */
export interface NewsDigest {
  topic: PortalTopic;
  summary: string;
  highlights: string[];
  articleCount: number;
  generatedAt: string;
}
