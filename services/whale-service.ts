import { apiFetch } from "@/lib/api-client";
import type { WhaleTransaction } from "@/types";

export async function fetchWhaleTransactions(): Promise<WhaleTransaction[]> {
  try {
    return await apiFetch<WhaleTransaction[]>("/api/whales/transactions");
  } catch {
    return [];
  }
}
