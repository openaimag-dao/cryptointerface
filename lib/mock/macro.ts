import type { MacroEvent, MacroIndicator } from "@/types";

export function getMockMacroIndicators(): MacroIndicator[] {
  return [
    {
      id: "dxy",
      label: "DXY Dollar Index",
      value: "104.32",
      changeLabel: "-0.18%",
      sentiment: "POSITIVE",
      description: "Weaker dollar historically correlates with crypto strength.",
    },
    {
      id: "us10y",
      label: "US 10Y Yield",
      value: "4.28%",
      changeLabel: "+0.04",
      sentiment: "NEGATIVE",
      description: "Rising yields increase opportunity cost of holding risk assets.",
    },
    {
      id: "cpi",
      label: "US CPI YoY",
      value: "3.1%",
      changeLabel: "-0.2pp",
      sentiment: "POSITIVE",
      description: "Cooling inflation supports the case for earlier rate cuts.",
    },
    {
      id: "vix",
      label: "VIX Volatility",
      value: "13.8",
      changeLabel: "-1.2%",
      sentiment: "NEUTRAL",
      description: "Low equity volatility, risk appetite remains stable.",
    },
    {
      id: "m2",
      label: "Global M2 Supply",
      value: "$103.4T",
      changeLabel: "+0.6% MoM",
      sentiment: "POSITIVE",
      description: "Expanding liquidity historically precedes crypto rallies with a lag.",
    },
    {
      id: "gold",
      label: "Gold Spot",
      value: "$2,384",
      changeLabel: "+0.3%",
      sentiment: "NEUTRAL",
      description: "Safe-haven demand remains steady alongside BTC's 'digital gold' narrative.",
    },
  ];
}

export function getMockMacroEvents(): MacroEvent[] {
  return [
    {
      id: "evt-1",
      title: "FOMC Interest Rate Decision",
      date: new Date(Date.now() + 1000 * 60 * 60 * 24 * 2).toISOString(),
      impact: "HIGH",
      forecast: "5.25% - 5.50%",
      previous: "5.25% - 5.50%",
    },
    {
      id: "evt-2",
      title: "US Non-Farm Payrolls",
      date: new Date(Date.now() + 1000 * 60 * 60 * 24 * 5).toISOString(),
      impact: "HIGH",
      forecast: "190K",
      previous: "175K",
    },
    {
      id: "evt-3",
      title: "US CPI m/m",
      date: new Date(Date.now() + 1000 * 60 * 60 * 24 * 9).toISOString(),
      impact: "MEDIUM",
      forecast: "0.3%",
      previous: "0.4%",
    },
    {
      id: "evt-4",
      title: "ECB Press Conference",
      date: new Date(Date.now() + 1000 * 60 * 60 * 24 * 12).toISOString(),
      impact: "MEDIUM",
      forecast: "-",
      previous: "-",
    },
  ];
}
