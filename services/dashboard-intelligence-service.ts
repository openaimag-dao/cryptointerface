import { apiFetch } from "@/lib/api-client";
import type { DashboardIntelligence } from "@/types";

export async function fetchDashboardIntelligence(
  symbol?: string,
  interval = "1h",
): Promise<DashboardIntelligence | null> {
  try {
    const params = new URLSearchParams({ interval });
    if (symbol) params.set("symbol", symbol);
    return await apiFetch<DashboardIntelligence>(`/api/dashboard/intelligence?${params.toString()}`);
  } catch {
    return null;
  }
}
