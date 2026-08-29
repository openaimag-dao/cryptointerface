import { apiFetch } from "@/lib/api-client";
import type { NewsItem, PortalNewsPage, PortalTopic } from "@/types";

export async function fetchNews(): Promise<NewsItem[]> {
  try {
    return await apiFetch<NewsItem[]>("/api/news");
  } catch {
    return [];
  }
}

export async function fetchPortalNews(
  topic?: PortalTopic,
  limit = 20,
  offset = 0,
): Promise<PortalNewsPage | null> {
  try {
    const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
    if (topic) params.set("topic", topic);
    return await apiFetch<PortalNewsPage>(`/api/news/portal?${params.toString()}`);
  } catch {
    return null;
  }
}

export async function fetchArticleById(id: string): Promise<NewsItem | null> {
  try {
    return await apiFetch<NewsItem>(`/api/news/${id}`);
  } catch {
    return null;
  }
}
