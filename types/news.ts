import type { Sentiment } from "./market";

export interface NewsItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  publishedAt: string;
  sentiment: Sentiment;
  tags: string[];
  url: string;
}
