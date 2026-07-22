import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchAssetTimeline } from "@/services/asset-service";
import type { AssetTimeline } from "@/types";

const TIMELINE: AssetTimeline = {
  symbol: "BTCUSDT",
  interval: "1h",
  entries: [
    {
      time: 1_700_000_000,
      score: 60,
      confidence: 70,
      direction: "LONG",
      changeSummary: "Confidence 50 -> 70",
      reasons: ["Open Interest rising"],
      strengthenedFactors: ["Open Interest"],
      weakenedFactors: [],
      dataStatus: "OK",
    },
  ],
};

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("fetchAssetTimeline", () => {
  it("requests the timeline endpoint with the given symbol and interval", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(TIMELINE), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);

    const result = await fetchAssetTimeline("BTC", "4h");

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/api/assets/BTC/timeline?interval=4h"),
      expect.any(Object),
    );
    expect(result).toEqual(TIMELINE);
  });

  it("returns null instead of throwing when the request fails", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("boom", { status: 500 }));
    vi.stubGlobal("fetch", fetchMock);

    const result = await fetchAssetTimeline("BTC");

    expect(result).toBeNull();
  });
});
