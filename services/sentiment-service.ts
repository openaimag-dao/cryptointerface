import { apiFetch } from "@/lib/api-client";
import type { SentimentSnapshot } from "@/types";

export async function fetchSentiment(symbol?: string, interval = "1h"): Promise<SentimentSnapshot | null> {
  try {
    const params = new URLSearchParams({ interval });
    if (symbol) params.set("symbol", symbol);
    return await apiFetch<SentimentSnapshot>(`/api/sentiment?${params.toString()}`);
  } catch {
    return null;
  }
}
