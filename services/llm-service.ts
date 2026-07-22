import { apiFetch } from "@/lib/api-client";
import type { LlmExplanation } from "@/types";

export async function fetchLlmExplanation(symbol: string, interval = "1h"): Promise<LlmExplanation | null> {
  try {
    return await apiFetch<LlmExplanation>(`/api/llm/explanation/${symbol}?interval=${interval}`);
  } catch {
    return null;
  }
}
