import type {
  AdminFetchLog,
  AdminNewsPage,
  AdminNewsUpdateRequest,
  AdminSource,
  AdminSourceUpdateRequest,
  EditorialStatus,
  EditorialStatusCounts,
  NewsItem,
} from "@/types";

export async function fetchAdminNews(status: EditorialStatus, limit = 20, offset = 0): Promise<AdminNewsPage> {
  const params = new URLSearchParams({ status, limit: String(limit), offset: String(offset) });
  const response = await fetch(`/api/admin/news?${params.toString()}`, { cache: "no-store" });
  if (!response.ok) return { items: [], total: 0, limit, offset };
  return response.json();
}

export async function fetchAdminNewsCounts(): Promise<EditorialStatusCounts["counts"] | null> {
  const response = await fetch("/api/admin/news/counts", { cache: "no-store" });
  if (!response.ok) return null;
  const data: EditorialStatusCounts = await response.json();
  return data.counts;
}

export async function updateAdminNews(articleId: string, payload: AdminNewsUpdateRequest): Promise<NewsItem | null> {
  const response = await fetch(`/api/admin/news/${articleId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) return null;
  return response.json();
}

export async function fetchAdminSources(): Promise<AdminSource[]> {
  const response = await fetch("/api/admin/sources", { cache: "no-store" });
  if (!response.ok) return [];
  return response.json();
}

export async function updateAdminSource(
  sourceId: string,
  payload: AdminSourceUpdateRequest,
): Promise<AdminSource | null> {
  const response = await fetch(`/api/admin/sources/${sourceId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) return null;
  return response.json();
}

export async function fetchAdminFetchLogs(limit = 50): Promise<AdminFetchLog[]> {
  const response = await fetch(`/api/admin/fetch-logs?limit=${limit}`, { cache: "no-store" });
  if (!response.ok) return [];
  return response.json();
}
