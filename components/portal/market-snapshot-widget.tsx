import { TrendingDown, TrendingUp } from "lucide-react";

import { cn } from "@/lib/utils";
import { macroLabel, type PortalLanguage } from "@/lib/portal-i18n";
import type { MacroIndicator } from "@/types";

interface MarketSnapshotWidgetProps {
  indicators: MacroIndicator[];
  title: string;
  lang: PortalLanguage;
}

// Fixed display order — indices first, then commodities, the way
// investing.com's own sidebar groups them. Anything the backend hasn't
// got a reading for yet (e.g. mid a Yahoo Finance hiccup — this data is
// free/keyless, no config to be missing) is just absent from
// `indicators` and skipped here, never shown as a placeholder.
const DISPLAY_ORDER = ["dow", "sp500", "nasdaq", "gold", "silver", "oil", "brent"];

// "+0.42%" / "-1.35%" / "—" (no prior reading yet) -> a signed number,
// or null for the no-data case. The backend's `sentiment` field encodes
// crypto-correlation direction (e.g. rising DXY reads as bearish for
// crypto), not literal up/down — this widget wants the literal number.
function parseChangePercent(changeLabel: string): number | null {
  const match = changeLabel.match(/^([+-])(\d+(?:\.\d+)?)%$/);
  if (!match) return null;
  return (match[1] === "-" ? -1 : 1) * Number(match[2]);
}

export function MarketSnapshotWidget({ indicators, title, lang }: MarketSnapshotWidgetProps) {
  const byId = new Map(indicators.map((indicator) => [indicator.id, indicator]));
  const rows = DISPLAY_ORDER.map((id) => byId.get(id)).filter((indicator) => indicator !== undefined);
  if (rows.length === 0) return null;

  return (
    <section className="glass-panel rounded-xl p-4">
      <div className="border-b border-border-strong pb-2.5">
        <h2 className="font-serif text-base font-semibold text-foreground">{title}</h2>
      </div>

      <ul className="mt-3 space-y-1.5">
        {rows.map((indicator) => {
          const changePercent = parseChangePercent(indicator.changeLabel);
          const isUp = changePercent !== null && changePercent >= 0;
          return (
            <li
              key={indicator.id}
              className="flex items-center justify-between gap-2 rounded-md px-1.5 py-1 text-sm"
            >
              <span className="font-medium text-foreground">{macroLabel(lang, indicator.id)}</span>
              <span className="flex shrink-0 items-center gap-2">
                <span className="font-tabular text-xs text-muted-foreground">{indicator.value}</span>
                {changePercent !== null ? (
                  <span
                    className={cn(
                      "flex items-center gap-0.5 font-tabular text-xs",
                      isUp ? "text-accent" : "text-danger",
                    )}
                  >
                    {isUp ? <TrendingUp className="size-3" /> : <TrendingDown className="size-3" />}
                    {indicator.changeLabel}
                  </span>
                ) : (
                  <span className="text-xs text-muted-foreground">{indicator.changeLabel}</span>
                )}
              </span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
