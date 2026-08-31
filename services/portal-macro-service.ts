import { API_BASE_URL } from "@/lib/env";
import type { MacroIndicator } from "@/types";

/**
 * Same real, public `/api/macro/indicators` endpoint the trading
 * terminal's macro grid reads (backend/app/api/macro.py) — indices and
 * commodities via Alpha Vantage ETF proxies (see backend/app/intelligence/
 * macro/symbols.py's docstring for why: none of these have a direct free
 * index/commodity feed). An indicator with no ANTHROPIC_API_KEY-style
 * missing-config problem of its own (ALPHA_VANTAGE_API_KEY) or that
 * hasn't had a successful poll cycle yet is simply absent from the
 * response, never a fabricated placeholder value. A long ISR window
 * matches how infrequently this data actually changes (the poller runs
 * every few hours, not every few seconds like crypto prices).
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
