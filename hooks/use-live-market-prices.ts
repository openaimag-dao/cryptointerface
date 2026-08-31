"use client";

import { useEffect, useState } from "react";

import { API_BASE_URL } from "@/lib/env";
import type { MarketAsset } from "@/types";

const POLL_INTERVAL_MS = 15_000;

/**
 * Starts from the server-rendered `initialAssets` (fast first paint, no
 * loading flash) and re-fetches the same real `/api/market` endpoint
 * client-side on an interval, so the price ticker and Market Movers
 * widget actually update while the tab is open — not just once per page
 * load/ISR revalidation. A failed poll just keeps showing the last good
 * snapshot rather than clearing it; this is a nice-to-have live refresh,
 * not something that should ever flash the UI to empty.
 */
export function useLiveMarketPrices(initialAssets: MarketAsset[]): MarketAsset[] {
  const [assets, setAssets] = useState(initialAssets);

  useEffect(() => {
    let cancelled = false;

    const poll = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/market`, { cache: "no-store" });
        if (!response.ok) return;
        const data: MarketAsset[] = await response.json();
        if (!cancelled && data.length > 0) setAssets(data);
      } catch {
        // Transient network hiccup — keep showing the last good snapshot.
      }
    };

    const id = setInterval(poll, POLL_INTERVAL_MS);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  return assets;
}
