import { apiFetch } from "@/lib/api-client";
import type { NewsDigest, NewsItem, PortalNewsPage, PortalTopic } from "@/types";

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

export async function searchNews(
  query: string,
  topic?: PortalTopic,
  limit = 30,
  offset = 0,
): Promise<PortalNewsPage | null> {
  try {
    const params = new URLSearchParams({ q: query, limit: String(limit), offset: String(offset) });
    if (topic) params.set("topic", topic);
    return await apiFetch<PortalNewsPage>(`/api/news/search?${params.toString()}`);
  } catch {
    return null;
  }
}

export async function fetchTrendingNews(topic?: PortalTopic, limit = 20): Promise<NewsItem[]> {
  try {
    const params = new URLSearchParams({ limit: String(limit) });
    if (topic) params.set("topic", topic);
    return await apiFetch<NewsItem[]>(`/api/news/trending?${params.toString()}`);
  } catch {
    return [];
  }
}

export async function fetchNewsDigest(topic: PortalTopic): Promise<NewsDigest | null> {
  try {
    return await apiFetch<NewsDigest>(`/api/news/digest?topic=${topic}`);
  } catch {
    return null;
  }
}
