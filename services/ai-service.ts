import { apiFetch } from "@/lib/api-client";
import type { AiDecision } from "@/types";

export async function fetchAiDecision(symbol: string, interval = "1h"): Promise<AiDecision | null> {
  try {
    return await apiFetch<AiDecision>(`/api/ai/decision/${symbol}?interval=${interval}`);
  } catch {
    // TanStack Query forbids a queryFn resolving to `undefined` — `null` is
    // the correct "no data yet" sentinel (e.g. symbol not backfilled yet).
    return null;
  }
}
