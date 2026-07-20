"use client";

import { useApiHealthPoll } from "@/hooks/use-api-health";
import { useMarketSocket } from "@/hooks/use-market-socket";

/** Mounts the shared `/ws/market` connection and the API health poll once
 * per app instance — both drive the header's connection status pills. */
export function MarketSocketProvider() {
  useMarketSocket();
  useApiHealthPoll();
  return null;
}
