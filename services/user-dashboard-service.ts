import type { NewsItem } from "@/types";

export async function fetchBookmarks(): Promise<NewsItem[]> {
  try {
    const response = await fetch("/api/user/bookmarks", { cache: "no-store" });
    if (!response.ok) return [];
    const data = await response.json();
    return data.items ?? [];
  } catch {
    return [];
  }
}

export async function addBookmark(articleId: string): Promise<boolean> {
  const response = await fetch(`/api/user/bookmarks/${articleId}`, { method: "POST" });
  return response.ok;
}

export async function removeBookmark(articleId: string): Promise<boolean> {
  const response = await fetch(`/api/user/bookmarks/${articleId}`, { method: "DELETE" });
  return response.ok;
}

export async function fetchWatchlist(): Promise<string[]> {
  try {
    const response = await fetch("/api/user/watchlist", { cache: "no-store" });
    if (!response.ok) return [];
    const data = await response.json();
    return data.symbols ?? [];
  } catch {
    return [];
  }
}

export async function addToWatchlist(symbol: string): Promise<string[] | null> {
  const response = await fetch("/api/user/watchlist", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ symbol }),
  });
  if (!response.ok) return null;
  const data = await response.json();
  return data.symbols;
}

export async function removeFromWatchlist(symbol: string): Promise<string[] | null> {
  const response = await fetch(`/api/user/watchlist/${symbol}`, { method: "DELETE" });
  if (!response.ok) return null;
  const data = await response.json();
  return data.symbols;
}
