import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import type { ReactNode } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { useAssetTimeline } from "@/hooks/use-asset";
import type { AssetTimeline } from "@/types";

vi.mock("@/services/asset-service", () => ({
  fetchAssetTimeline: vi.fn(),
}));

import { fetchAssetTimeline } from "@/services/asset-service";

const TIMELINE: AssetTimeline = { symbol: "BTCUSDT", interval: "1h", entries: [] };

function wrapper({ children }: { children: ReactNode }) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}

afterEach(() => {
  vi.mocked(fetchAssetTimeline).mockReset();
});

describe("useAssetTimeline", () => {
  it("fetches the timeline for the given symbol/interval", async () => {
    vi.mocked(fetchAssetTimeline).mockResolvedValue(TIMELINE);

    const { result } = renderHook(() => useAssetTimeline("BTC", "1h"), { wrapper });

    await waitFor(() => expect(result.current.data).toEqual(TIMELINE));
    expect(fetchAssetTimeline).toHaveBeenCalledWith("BTC", "1h");
  });

  it("stays disabled without a symbol", () => {
    const { result } = renderHook(() => useAssetTimeline(""), { wrapper });

    expect(result.current.fetchStatus).toBe("idle");
    expect(fetchAssetTimeline).not.toHaveBeenCalled();
  });
});
