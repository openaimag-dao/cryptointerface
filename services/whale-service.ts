import { getMockWhaleTransactions } from "@/lib/mock/whales";
import { mockDelay } from "@/lib/mock/delay";
import type { WhaleTransaction } from "@/types";

export async function fetchWhaleTransactions(): Promise<WhaleTransaction[]> {
  return mockDelay(getMockWhaleTransactions());
}
