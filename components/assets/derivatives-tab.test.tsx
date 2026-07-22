import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { DerivativesTab } from "@/components/assets/derivatives-tab";
import type { AssetDerivatives } from "@/types";

vi.mock("@/hooks/use-asset", () => ({
  useAssetDerivatives: vi.fn(),
}));

import { useAssetDerivatives } from "@/hooks/use-asset";

const DERIVATIVES: AssetDerivatives = {
  symbol: "BTCUSDT",
  fundingRate: 0.0001,
  fundingHistory: [],
  fundingTrend: "UP",
  openInterest: 5000,
  openInterestValue: 750000,
  oiDeltaPercent: 5,
  liquidationClusters: [
    { priceLow: 60000, priceHigh: 61000, totalUsd: 100000, eventCount: 4 },
    { priceLow: 61000, priceHigh: 62000, totalUsd: 500000, eventCount: 10 },
  ],
  exchangeBreakdown: [
    { exchange: "Binance", status: "AVAILABLE", openInterest: 5000, fundingRate: 0.0001, note: "Live USDT-M Futures data." },
    { exchange: "Bybit", status: "NOT_YET_IMPLEMENTED", openInterest: null, fundingRate: null, note: "No client integrated for this exchange yet." },
  ],
};

afterEach(() => {
  vi.mocked(useAssetDerivatives).mockReset();
});

describe("DerivativesTab", () => {
  it("renders the exchange breakdown with real and not-yet-implemented rows", () => {
    vi.mocked(useAssetDerivatives).mockReturnValue({
      data: DERIVATIVES,
      isLoading: false,
    } as ReturnType<typeof useAssetDerivatives>);

    render(<DerivativesTab baseAsset="BTC" />);

    expect(screen.getByText("Binance")).toBeInTheDocument();
    expect(screen.getByText("Live")).toBeInTheDocument();
    expect(screen.getByText("Bybit")).toBeInTheDocument();
    expect(screen.getByText("Not yet implemented")).toBeInTheDocument();
  });

  it("renders the liquidation heat map from real cluster data", () => {
    vi.mocked(useAssetDerivatives).mockReturnValue({
      data: DERIVATIVES,
      isLoading: false,
    } as ReturnType<typeof useAssetDerivatives>);

    render(<DerivativesTab baseAsset="BTC" />);

    expect(screen.getByRole("img", { name: /liquidation heat map/i })).toBeInTheDocument();
  });
});
