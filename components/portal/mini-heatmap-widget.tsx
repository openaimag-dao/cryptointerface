"use client";

import Link from "next/link";

import { cn } from "@/lib/utils";
import { useLiveMarketPrices } from "@/hooks/use-live-market-prices";
import type { MarketAsset } from "@/types";

interface MiniHeatmapWidgetProps {
  assets: MarketAsset[];
  title: string;
}

// Strips the USDT quote suffix for display — "BTCUSDT" -> "BTC".
function baseSymbol(symbol: string): string {
  return symbol.replace(/USDT$/, "");
}

// Tile opacity scales with |change%|, capped at an 8% intraday move —
// past that, more saturation wouldn't add legible signal.
function intensity(changePercent: number): number {
  return Math.min(1, Math.abs(changePercent) / 8) * 0.6 + 0.12;
}

// Same live-updating watchlist snapshot MarketMoversWidget reads
// (/api/market via useLiveMarketPrices), shown as a grid of colored
// tiles instead of a ranked gainers/losers list — the "at a glance"
// heatmap real crypto portals put next to their headlines.
export function MiniHeatmapWidget({ assets: initialAssets, title }: MiniHeatmapWidgetProps) {
  const assets = useLiveMarketPrices(initialAssets);
  if (assets.length === 0) return null;

  return (
    <section className="glass-panel rounded-xl p-4">
      <div className="border-b border-border-strong pb-2.5">
        <h2 className="font-serif text-base font-semibold text-foreground">{title}</h2>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-1.5">
        {assets.map((asset) => {
          const isUp = asset.changePercent24h >= 0;
          const pct = Math.round(intensity(asset.changePercent24h) * 100);
          return (
            <Link
              key={asset.symbol}
              href={`/search?q=${baseSymbol(asset.symbol)}`}
              className="rounded-md px-2 py-2 transition-transform hover:scale-[1.02]"
              style={{
                backgroundColor: `color-mix(in srgb, var(--${isUp ? "accent" : "danger"}) ${pct}%, transparent)`,
              }}
            >
              <div className="text-xs font-semibold text-foreground">{baseSymbol(asset.symbol)}</div>
              <div className={cn("font-tabular text-[11px]", isUp ? "text-accent" : "text-danger")}>
                {isUp ? "+" : ""}
                {asset.changePercent24h.toFixed(2)}%
              </div>
            </Link>
          );
        })}
      </div>
    </section>
  );
}
