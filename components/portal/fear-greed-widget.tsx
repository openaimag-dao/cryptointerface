import { portalStrings, type PortalLanguage } from "@/lib/portal-i18n";
import type { MacroIndicator } from "@/types";

interface FearGreedWidgetProps {
  indicators: MacroIndicator[];
  lang: PortalLanguage;
}

// Same 0-24/25-49/50-74/75-100-ish buckets alternative.me's own gauge
// uses — a presentational classification only. The backend
// (app/api/macro.py) deliberately keeps fear_greed's `sentiment` field
// NEUTRAL (level-based, not change-based — see score_macro()'s
// docstring); this label is this widget's own read of the level, not a
// value carried over the wire.
function classify(value: number, t: ReturnType<typeof portalStrings>): string {
  if (value < 25) return t.fearGreedExtremeFear;
  if (value < 45) return t.fearGreedFear;
  if (value < 55) return t.fearGreedNeutral;
  if (value < 75) return t.fearGreedGreed;
  return t.fearGreedExtremeGreed;
}

export function FearGreedWidget({ indicators, lang }: FearGreedWidgetProps) {
  const t = portalStrings(lang);
  const indicator = indicators.find((i) => i.id === "fear_greed");
  const value = indicator ? Number(indicator.value) : NaN;
  if (!Number.isFinite(value)) return null;
  const clamped = Math.min(100, Math.max(0, value));

  return (
    <section className="glass-panel rounded-xl p-4">
      <div className="border-b border-border-strong pb-2.5">
        <h2 className="font-serif text-base font-semibold text-foreground">{t.fearGreedTitle}</h2>
      </div>

      <div className="mt-4 px-1">
        <div className="flex items-baseline justify-between">
          <span className="font-tabular text-3xl font-semibold text-foreground">{clamped.toFixed(0)}</span>
          <span className="text-xs font-medium text-muted-foreground">{classify(clamped, t)}</span>
        </div>
        <div className="relative mt-4 h-2 w-full rounded-full bg-gradient-to-r from-danger via-warning to-accent">
          <span
            className="absolute -top-1 size-4 -translate-x-1/2 rounded-full border-2 border-background bg-foreground shadow-sm"
            style={{ left: `${clamped}%` }}
          />
        </div>
      </div>
    </section>
  );
}
