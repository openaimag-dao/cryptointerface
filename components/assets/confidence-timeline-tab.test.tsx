import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ConfidenceTimelineTab } from "@/components/assets/confidence-timeline-tab";
import type { AssetTimeline } from "@/types";

vi.mock("@/hooks/use-asset", () => ({
  useAssetTimeline: vi.fn(),
}));

import { useAssetTimeline } from "@/hooks/use-asset";

const TIMELINE: AssetTimeline = {
  symbol: "BTCUSDT",
  interval: "1h",
  entries: [
    {
      time: 1_700_000_000,
      score: 65,
      confidence: 78,
      direction: "LONG",
      changeSummary: "Confidence 60 → 78",
      reasons: ["Open Interest rose sharply", "EMA trend confirmed"],
      strengthenedFactors: ["Open Interest", "Trend"],
      weakenedFactors: ["News"],
      dataStatus: "OK",
    },
    {
      time: 1_699_990_000,
      score: 50,
      confidence: 50,
      direction: "WAIT",
      changeSummary: null,
      reasons: null,
      strengthenedFactors: [],
      weakenedFactors: [],
      dataStatus: "AWAITING_DATA",
    },
  ],
};

afterEach(() => {
  vi.mocked(useAssetTimeline).mockReset();
});

function mockTimeline(data: AssetTimeline | null, isLoading = false) {
  vi.mocked(useAssetTimeline).mockReturnValue({ data, isLoading } as ReturnType<typeof useAssetTimeline>);
}

describe("ConfidenceTimelineTab", () => {
  it("shows a skeleton while loading", () => {
    mockTimeline(undefined as unknown as AssetTimeline, true);

    const { container } = render(<ConfidenceTimelineTab baseAsset="BTC" />);

    expect(container.querySelectorAll('[class*="animate-pulse"]').length).toBeGreaterThan(0);
  });

  it("renders each timeline entry's change summary", () => {
    mockTimeline(TIMELINE);

    render(<ConfidenceTimelineTab baseAsset="BTC" />);

    expect(screen.getByText("Confidence 60 → 78")).toBeInTheDocument();
    // Falls back to a plain score/confidence summary when the backend didn't send one.
    expect(screen.getByText("Market Score 50, Confidence 50%")).toBeInTheDocument();
  });

  it("opens the Explain Decision modal with real reasons and factor deltas on click", async () => {
    mockTimeline(TIMELINE);
    const user = userEvent.setup();

    render(<ConfidenceTimelineTab baseAsset="BTC" />);

    const buttons = screen.getAllByRole("button", { name: /Почему AI изменил мнение/i });
    await user.click(buttons[0]);

    const dialog = await screen.findByRole("dialog");
    expect(within(dialog).getByText("Open Interest rose sharply")).toBeInTheDocument();
    expect(within(dialog).getByText("EMA trend confirmed")).toBeInTheDocument();
    expect(within(dialog).getByText("Open Interest", { selector: "li" })).toBeInTheDocument();
    expect(within(dialog).getByText("News", { selector: "li" })).toBeInTheDocument();
  });

  it("shows an honest awaiting-data message instead of fabricating reasons", async () => {
    mockTimeline(TIMELINE);
    const user = userEvent.setup();

    render(<ConfidenceTimelineTab baseAsset="BTC" />);

    const buttons = screen.getAllByRole("button", { name: /Почему AI изменил мнение/i });
    await user.click(buttons[1]);

    const dialog = await screen.findByRole("dialog");
    expect(
      within(dialog).getByText(/recorded before per-factor reasons were captured/i),
    ).toBeInTheDocument();
  });
});
