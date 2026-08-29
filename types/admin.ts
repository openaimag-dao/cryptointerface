import type { NewsItem } from "./news";

/**
 * Mirrors backend/app/models/news.py::EDITORIAL_STATUSES — keep in sync.
 */
export const EDITORIAL_STATUSES = [
  "IMPORTED",
  "PROCESSING",
  "PENDING_REVIEW",
  "APPROVED",
  "PUBLISHED",
  "REJECTED",
  "ARCHIVED",
] as const;

export type EditorialStatus = (typeof EDITORIAL_STATUSES)[number];

export interface AdminNewsPage {
  items: NewsItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface EditorialStatusCounts {
  counts: Record<EditorialStatus, number>;
}

export interface AdminNewsUpdateRequest {
  title?: string;
  summary?: string;
  category?: string;
  portalTopic?: string;
  editorialStatus?: EditorialStatus;
}
