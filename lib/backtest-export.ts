import type { BacktestReport, BacktestTrade } from "@/types";

const CSV_COLUMNS = [
  "date",
  "symbol",
  "direction",
  "entryPrice",
  "exitPrice",
  "pnl",
  "pnlPercent",
  "durationSeconds",
  "exitReason",
  "decisionScore",
  "confidence",
  "plannedRiskReward",
] as const;

function csvEscape(value: string): string {
  return /[",\n]/.test(value) ? `"${value.replace(/"/g, '""')}"` : value;
}

/** Same columns as the backend's report_generator.py::generate_csv_report(),
 * built client-side from the trades already loaded on the page. */
export function tradesToCsv(trades: BacktestTrade[]): string {
  const rows = trades.map((t) =>
    [
      new Date(t.entryTime * 1000).toISOString(),
      t.symbol,
      t.direction,
      t.entryPrice,
      t.exitPrice,
      t.pnl,
      t.pnlPercent,
      t.durationSeconds,
      t.exitReason,
      t.decisionScore,
      t.confidence,
      t.plannedRiskReward,
    ]
      .map((value) => csvEscape(String(value)))
      .join(","),
  );
  return [CSV_COLUMNS.join(","), ...rows].join("\n");
}

export function reportToJson(report: BacktestReport, trades: BacktestTrade[]): string {
  return JSON.stringify({ ...report, trades }, null, 2);
}
