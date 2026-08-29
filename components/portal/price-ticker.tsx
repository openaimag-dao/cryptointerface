import Link from "next/link";
import { TrendingDown, TrendingUp } from "lucide-react";

import { cn, formatCurrency, formatPercent } from "@/lib/utils";
import { fetchPortalPrices } from "@/services/portal-market-service";

// Strips the USDT quote suffix for display — "BTCUSDT" -> "BTC".
function baseSymbol(symbol: string): string {
  return symbol.replace(/USDT$/, "");
}

export async function PriceTicker() {
  const assets = await fetchPortalPrices();
  if (assets.length === 0) return null;

  return (
    <div className="border-b border-border-strong bg-surface/60">
      <div className="mx-auto flex max-w-6xl gap-6 overflow-x-auto px-6 py-2 text-xs">
        {assets.map((asset) => {
          const isUp = asset.changePercent24h >= 0;
          return (
            <Link
              key={asset.symbol}
              href={`/assets/${asset.symbol}`}
              className="flex shrink-0 items-center gap-1.5 font-tabular text-muted-foreground transition-colors hover:text-foreground"
            >
              <span className="font-semibold text-foreground">{baseSymbol(asset.symbol)}</span>
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
