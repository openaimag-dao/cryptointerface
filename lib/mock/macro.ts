import type { MacroEvent } from "@/types";

// Economic calendar only — /api/macro/indicators is real (see
// services/macro-service.ts). This still needs its own provider.
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
