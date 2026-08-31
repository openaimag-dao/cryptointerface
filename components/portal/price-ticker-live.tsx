"use client";

import Link from "next/link";
import { TrendingDown, TrendingUp } from "lucide-react";

import { cn, formatCurrency, formatPercent } from "@/lib/utils";
import { useLiveMarketPrices } from "@/hooks/use-live-market-prices";
import type { MarketAsset } from "@/types";

// Strips the USDT quote suffix for display — "BTCUSDT" -> "BTC".
function baseSymbol(symbol: string): string {
  return symbol.replace(/USDT$/, "");
}

export function PriceTickerLive({ initialAssets }: { initialAssets: MarketAsset[] }) {
  const assets = useLiveMarketPrices(initialAssets);

  return (
    <div className="border-b border-border-strong bg-surface/60">
      <div className="mx-auto flex max-w-screen-2xl gap-6 overflow-x-auto px-6 py-2 text-xs">
        {assets.map((asset) => {
          const isUp = asset.changePercent24h >= 0;
          const symbol = baseSymbol(asset.symbol);
          return (
            // The portal is fully public — /assets/[symbol] lives under
            // the private terminal's Basic-Auth-gated route group, so a
            // reader clicking a ticker symbol would hit a login wall.
            // Search is the portal's own equivalent lookup.
            <Link
              key={asset.symbol}
              href={`/search?q=${symbol}`}
              className="flex shrink-0 items-center gap-1.5 font-tabular text-muted-foreground transition-colors hover:text-foreground"
            >
              <span className="font-semibold text-foreground">{symbol}</span>
              <span>{formatCurrency(asset.price)}</span>
              <span className={cn("flex items-center gap-0.5", isUp ? "text-accent" : "text-danger")}>
                {isUp ? <TrendingUp className="size-3" /> : <TrendingDown className="size-3" />}
                {formatPercent(asset.changePercent24h)}
              </span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
