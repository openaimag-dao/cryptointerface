"use client";

import Link from "next/link";
import { TrendingDown, TrendingUp } from "lucide-react";

import { cn, formatCurrency, formatPercent } from "@/lib/utils";
import { useLiveMarketPrices } from "@/hooks/use-live-market-prices";
import type { MarketAsset } from "@/types";

interface MarketMoversWidgetProps {
  assets: MarketAsset[];
  title: string;
  gainersLabel: string;
  losersLabel: string;
}

// Strips the USDT quote suffix for display — "BTCUSDT" -> "BTC".
function baseSymbol(symbol: string): string {
  return symbol.replace(/USDT$/, "");
}

// Same "block in block" sidebar module as HeadlineListWidget, but for the
// live market — real 24h change from the same /api/market feed the price
// ticker reads, ranked rather than narrated, the way a crypto portal's
// market panel actually looks next to its headlines. `assets` is the
// server-rendered snapshot for first paint; useLiveMarketPrices takes it
// from there and re-ranks on every live poll.
export function MarketMoversWidget({ assets: initialAssets, title, gainersLabel, losersLabel }: MarketMoversWidgetProps) {
  const assets = useLiveMarketPrices(initialAssets);
  if (assets.length === 0) return null;

  const sorted = [...assets].sort((a, b) => b.changePercent24h - a.changePercent24h);
  const gainers = sorted.slice(0, 3);
  const losers = sorted.slice(-3).reverse();

  return (
    <section className="glass-panel rounded-xl p-4">
      <div className="border-b border-border-strong pb-2.5">
        <h2 className="font-serif text-base font-semibold text-foreground">{title}</h2>
      </div>

      <div className="mt-3 space-y-4">
        <MoversList label={gainersLabel} assets={gainers} />
        <MoversList label={losersLabel} assets={losers} />
      </div>
    </section>
  );
}

function MoversList({ label, assets }: { label: string; assets: MarketAsset[] }) {
  return (
    <div>
      <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">{label}</h3>
      <ul className="mt-1.5 space-y-1.5">
        {assets.map((asset) => {
          const isUp = asset.changePercent24h >= 0;
          return (
            <li key={asset.symbol}>
              <Link
                href={`/search?q=${baseSymbol(asset.symbol)}`}
                className="flex items-center justify-between gap-2 rounded-md px-1.5 py-1 text-sm transition-colors hover:bg-white/[0.04]"
              >
                <span className="font-semibold text-foreground">{baseSymbol(asset.symbol)}</span>
                <span className="font-tabular text-xs text-muted-foreground">{formatCurrency(asset.price)}</span>
                <span className={cn("flex shrink-0 items-center gap-0.5 font-tabular text-xs", isUp ? "text-accent" : "text-danger")}>
                  {isUp ? <TrendingUp className="size-3" /> : <TrendingDown className="size-3" />}
                  {formatPercent(asset.changePercent24h)}
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
