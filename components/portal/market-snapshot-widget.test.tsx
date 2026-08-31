import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { MarketSnapshotWidget } from "@/components/portal/market-snapshot-widget";
import type { MacroIndicator } from "@/types";

function indicator(overrides: Partial<MacroIndicator>): MacroIndicator {
  return {
    id: "sp500",
    label: "S&P 500 (SPY proxy)",
    value: "$650.00",
    changeLabel: "+0.42%",
    sentiment: "NEUTRAL",
    description: "",
    ...overrides,
  };
}

describe("MarketSnapshotWidget", () => {
  it("renders only the indicators the backend actually returned, in the fixed display order", () => {
    // Backend order here is deliberately scrambled and missing dow/silver/
    // brent (e.g. no ALPHA_VANTAGE_API_KEY yet, or mid rate-limit) — the
    // widget must still show what it has, in its own fixed order, and
    // never a placeholder for what it doesn't.
    render(
      <MarketSnapshotWidget
        indicators={[
          indicator({ id: "nasdaq", label: "NASDAQ 100 (QQQ proxy)", value: "$610.00", changeLabel: "-1.10%" }),
          indicator({ id: "gold", label: "Gold Spot (GLD proxy)", value: "$310.00", changeLabel: "+0.15%" }),
          indicator({ id: "sp500" }),
        ]}
        title="Markets"
        lang="en"
      />,
    );

    const items = screen.getAllByRole("listitem").map((el) => el.textContent);
    expect(items).toEqual([
      expect.stringContaining("S&P 500"),
      expect.stringContaining("Nasdaq"),
      expect.stringContaining("Gold"),
    ]);
    expect(screen.queryByText(/dow jones/i)).not.toBeInTheDocument();
  });

  it("shows a plain dash for an indicator with no prior reading yet, not a fabricated change", () => {
    render(
      <MarketSnapshotWidget
        indicators={[indicator({ id: "dow", label: "Dow Jones (DIA proxy)", value: "$450.00", changeLabel: "—" })]}
        title="Markets"
        lang="en"
      />,
    );

    expect(screen.getByText("—")).toBeInTheDocument();
  });

  it("renders nothing when no indicator has data yet", () => {
    const { container } = render(<MarketSnapshotWidget indicators={[]} title="Markets" lang="en" />);
    expect(container).toBeEmptyDOMElement();
  });

  it("uses localized labels for the given language", () => {
    render(
      <MarketSnapshotWidget
        indicators={[indicator({ id: "gold", label: "Gold Spot (GLD proxy)" })]}
        title="Рынки"
        lang="ru"
      />,
    );

    expect(screen.getByText("Золото")).toBeInTheDocument();
  });
});
