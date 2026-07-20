import { getMockAiAnalysis, getMockSignals } from "@/lib/mock/signals";
import { mockDelay } from "@/lib/mock/delay";
import type { AiAnalysis, AiSignal } from "@/types";

export async function fetchSignals(): Promise<AiSignal[]> {
  return mockDelay(getMockSignals());
}

export async function fetchAiAnalysis(symbol: string): Promise<AiAnalysis> {
  return mockDelay(getMockAiAnalysis(symbol));
}
