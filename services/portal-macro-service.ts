import { API_BASE_URL } from "@/lib/env";
import type { MacroIndicator } from "@/types";

/**
 * Same real, public `/api/macro/indicators` endpoint the trading
 * terminal's macro grid reads (backend/app/api/macro.py) — real indices/
 * commodities/yields from Yahoo Finance's free, keyless chart endpoint
 * (see backend/app/intelligence/macro/symbols.py's docstring). An
 * indicator that hasn't had a successful poll cycle yet is simply absent
 * from the response, never a fabricated placeholder value. A longer ISR
 * window than the price ticker's matches how infrequently this data
 * actually changes (the poller runs every 30 minutes, not every few
 * seconds like crypto prices).
 */
export async function fetchPortalMacroIndicators(): Promise<MacroIndicator[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/macro/indicators`, { next: { revalidate: 600 } });
    if (!response.ok) return [];
    return await response.json();
  } catch {
    return [];
  }
}
