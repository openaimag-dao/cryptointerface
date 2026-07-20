import { getMockMacroEvents, getMockMacroIndicators } from "@/lib/mock/macro";
import { mockDelay } from "@/lib/mock/delay";
import type { MacroEvent, MacroIndicator } from "@/types";

export async function fetchMacroIndicators(): Promise<MacroIndicator[]> {
  return mockDelay(getMockMacroIndicators());
}

export async function fetchMacroEvents(): Promise<MacroEvent[]> {
  return mockDelay(getMockMacroEvents());
}
