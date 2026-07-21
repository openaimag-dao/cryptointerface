import { apiFetch } from "@/lib/api-client";
import type { AiSignal } from "@/types";

export async function fetchSignals(): Promise<AiSignal[]> {
  return apiFetch<AiSignal[]>("/api/signals");
}
