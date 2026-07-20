import { getMockSignals } from "@/lib/mock/signals";
import { mockDelay } from "@/lib/mock/delay";
import type { AiSignal } from "@/types";

export async function fetchSignals(): Promise<AiSignal[]> {
  return mockDelay(getMockSignals());
}
