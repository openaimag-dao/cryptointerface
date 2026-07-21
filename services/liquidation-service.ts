import { apiFetch } from "@/lib/api-client";
import type { LiquidationEvent, LiquidationHeatmapCell, LiquidationTotals } from "@/types";

export async function fetchLiquidations(count = 30): Promise<LiquidationEvent[]> {
  return apiFetch<LiquidationEvent[]>(`/api/liquidations?count=${count}`);
}

export async function fetchLiquidationHeatmap(symbol = "BTCUSDT", count = 40): Promise<LiquidationHeatmapCell[]> {
  return apiFetch<LiquidationHeatmapCell[]>(`/api/liquidations/heatmap?symbol=${symbol}&count=${count}`);
}

export async function fetchLiquidationTotals(): Promise<LiquidationTotals> {
  return apiFetch<LiquidationTotals>("/api/liquidations/totals");
}
