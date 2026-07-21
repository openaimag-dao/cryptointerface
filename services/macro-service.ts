import { apiFetch } from "@/lib/api-client";
import { getMockMacroEvents } from "@/lib/mock/macro";
import { mockDelay } from "@/lib/mock/delay";
import type { MacroEvent, MacroIndicator } from "@/types";

export async function fetchMacroIndicators(): Promise<MacroIndicator[]> {
  try {
    return await apiFetch<MacroIndicator[]>("/api/macro/indicators");
  } catch {
    return [];
  }
}

// Economic calendar (FOMC/NFP/CPI dates) still needs its own provider —
// see backend/app/api/macro.py's docstring. Real indicators above.
export async function fetchMacroEvents(): Promise<MacroEvent[]> {
  return mockDelay(getMockMacroEvents());
}
