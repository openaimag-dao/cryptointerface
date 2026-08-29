import { API_BASE_URL } from "@/lib/env";
import type { MarketAsset } from "@/types";

/**
 * The portal's price ticker reads the same real, public `/api/market`
 * endpoint the trading terminal uses (Binance-backed, no auth required —
 * see backend/app/api/market.py) — not a separate/mocked feed. Uses a
 * short ISR revalidate window rather than `no-store`: a public news page
 * doesn't need per-request freshness, and this keeps a busy portal from
 * hammering the backend on every page view.
 */
export async function fetchPortalPrices(): Promise<MarketAsset[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/market`, { next: { revalidate: 15 } });
    if (!response.ok) return [];
    return await response.json();
  } catch {
    return [];
  }
}
