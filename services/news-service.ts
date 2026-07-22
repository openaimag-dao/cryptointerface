import { apiFetch } from "@/lib/api-client";
import type { NewsItem } from "@/types";

export async function fetchNews(): Promise<NewsItem[]> {
  try {
    return await apiFetch<NewsItem[]>("/api/news");
  } catch {
    return [];
  }
}
