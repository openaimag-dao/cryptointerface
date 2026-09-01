import { apiFetch } from "@/lib/api-client";
import type { EntityNewsPage, NewsDigest, NewsItem, PortalNewsPage, PortalTopic } from "@/types";
import type { PortalLanguage } from "@/lib/portal-i18n";

function withLang(params: URLSearchParams, lang?: PortalLanguage): URLSearchParams {
  if (lang && lang !== "en") params.set("lang", lang);
  return params;
}

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
  lang?: PortalLanguage,
): Promise<PortalNewsPage | null> {
  try {
    const params = withLang(new URLSearchParams({ limit: String(limit), offset: String(offset) }), lang);
    if (topic) params.set("topic", topic);
    return await apiFetch<PortalNewsPage>(`/api/news/portal?${params.toString()}`);
  } catch {
    return null;
  }
}

export async function fetchArticleById(id: string, lang?: PortalLanguage): Promise<NewsItem | null> {
  try {
    const params = withLang(new URLSearchParams(), lang);
    const query = params.toString();
    return await apiFetch<NewsItem>(`/api/news/${id}${query ? `?${query}` : ""}`);
  } catch {
    return null;
  }
}

export async function searchNews(
  query: string,
  topic?: PortalTopic,
  limit = 30,
  offset = 0,
  lang?: PortalLanguage,
): Promise<PortalNewsPage | null> {
  try {
    const params = withLang(
      new URLSearchParams({ q: query, limit: String(limit), offset: String(offset) }),
      lang,
    );
    if (topic) params.set("topic", topic);
    return await apiFetch<PortalNewsPage>(`/api/news/search?${params.toString()}`);
  } catch {
    return null;
  }
}

export async function fetchTrendingNews(topic?: PortalTopic, limit = 20, lang?: PortalLanguage): Promise<NewsItem[]> {
  try {
    const params = withLang(new URLSearchParams({ limit: String(limit) }), lang);
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

export async function fetchTagNews(
  slug: string,
  limit = 20,
  offset = 0,
  lang?: PortalLanguage,
): Promise<EntityNewsPage | null> {
  try {
    const params = withLang(new URLSearchParams({ limit: String(limit), offset: String(offset) }), lang);
    return await apiFetch<EntityNewsPage>(`/api/news/tag/${encodeURIComponent(slug)}?${params.toString()}`);
  } catch {
    return null;
  }
}
