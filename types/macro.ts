export interface MacroIndicator {
  id: string;
  label: string;
  value: string;
  changeLabel: string;
  sentiment: "POSITIVE" | "NEGATIVE" | "NEUTRAL";
  description: string;
}

export interface MacroEvent {
  id: string;
  title: string;
  date: string;
  impact: "HIGH" | "MEDIUM" | "LOW";
  forecast: string;
  previous: string;
}
