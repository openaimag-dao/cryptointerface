import { getMockLiquidationHeatmap, getMockLiquidations } from "@/lib/mock/liquidations";
import { mockDelay } from "@/lib/mock/delay";
import type { LiquidationEvent, LiquidationHeatmapCell } from "@/types";

export async function fetchLiquidations(): Promise<LiquidationEvent[]> {
  return mockDelay(getMockLiquidations());
}

export async function fetchLiquidationHeatmap(): Promise<LiquidationHeatmapCell[]> {
  return mockDelay(getMockLiquidationHeatmap());
}
