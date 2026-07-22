"use client";

import { memo } from "react";
import { motion } from "framer-motion";
import { Pin, StickyNote, X } from "lucide-react";

import { cn, formatCompactNumber, formatCurrency, formatPercent } from "@/lib/utils";
import type { AssetQuote } from "@/types";
import { useWatchlistStore } from "@/store/watchlist-store";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { DirectionBadge } from "@/components/common/direction-badge";
import { AiScoreRing } from "@/components/common/ai-score-ring";

interface AssetCardProps {
  asset: AssetQuote;
  index?: number;
  /** Show pin/remove/note controls — only meaningful when this card
   * represents a real entry in the user's watchlist, not the default
   * fallback list shown before they've added anything. */
  showWatchlistControls?: boolean;
}

function AssetCardImpl({ asset, index = 0, showWatchlistControls = false }: AssetCardProps) {
  const isUp = asset.changePercent24h >= 0;
  const item = useWatchlistStore((state) => state.items[asset.symbol]);
  const removeSymbol = useWatchlistStore((state) => state.removeSymbol);
  const togglePin = useWatchlistStore((state) => state.togglePin);
  const setNote = useWatchlistStore((state) => state.setNote);

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
    >
      <Card className="group relative overflow-hidden p-5 transition-colors hover:border-border-strong focus-within:border-border-strong">
        <div
          className={cn(
            "pointer-events-none absolute inset-x-0 top-0 h-24 opacity-0 transition-opacity duration-300 group-hover:opacity-100",
            isUp ? "bg-gradient-to-b from-accent/10 to-transparent" : "bg-gradient-to-b from-danger/10 to-transparent",
          )}
        />

        {showWatchlistControls && item ? (
          <div className="absolute right-3 top-3 z-10 flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100">
            <Popover>
              <PopoverTrigger asChild>
                <Button variant="ghost" size="icon" className="size-6" title="Note" aria-label={`Note for ${asset.symbol}`}>
                  <StickyNote className={cn("size-3.5", item.note && "text-accent")} />
                </Button>
              </PopoverTrigger>
              <PopoverContent align="end">
                <label htmlFor={`watchlist-note-${asset.symbol}`} className="sr-only">
                  Note for {asset.symbol}
                </label>
                <textarea
                  id={`watchlist-note-${asset.symbol}`}
                  defaultValue={item.note}
                  onBlur={(e) => setNote(asset.symbol, e.target.value)}
                  placeholder="Add a note…"
                  rows={3}
                  className="w-full resize-none rounded-md border border-border-subtle bg-white/[0.03] px-3 py-2 text-xs text-foreground outline-none placeholder:text-muted-foreground focus-visible:border-accent/50"
                />
              </PopoverContent>
            </Popover>
            <Button
              variant="ghost"
              size="icon"
              className="size-6"
              title={item.pinned ? "Unpin" : "Pin"}
              aria-label={item.pinned ? `Unpin ${asset.symbol}` : `Pin ${asset.symbol}`}
              aria-pressed={item.pinned}
              onClick={() => togglePin(asset.symbol)}
            >
              <Pin className={cn("size-3.5", item.pinned && "fill-current text-accent")} />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="size-6"
              title="Remove from watchlist"
              aria-label={`Remove ${asset.symbol} from watchlist`}
              onClick={() => removeSymbol(asset.symbol)}
            >
              <X className="size-3.5" />
            </Button>
          </div>
        ) : null}

        <div className="relative flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-semibold text-foreground">{asset.symbol}</span>
              <DirectionBadge direction={asset.direction} size="sm" />
            </div>
            <p className="mt-0.5 text-xs text-muted-foreground">{asset.name}</p>
          </div>
          <AiScoreRing score={asset.aiScore} size={48} strokeWidth={3.5} />
        </div>

        <div className="relative mt-4 flex items-end justify-between">
          <div>
            <p className="font-tabular text-2xl font-semibold tracking-tight text-foreground">
              {formatCurrency(asset.price)}
            </p>
            <p className={cn("mt-1 font-tabular text-xs font-medium", isUp ? "text-accent" : "text-danger")}>
              {formatPercent(asset.changePercent24h)} (24h)
            </p>
          </div>
          <div className="text-right text-xs text-muted-foreground">
            <p className="font-tabular">Vol {formatCompactNumber(asset.volume24h)}</p>
            <p className="font-tabular">OI {formatCompactNumber(asset.openInterest)}</p>
          </div>
        </div>
      </Card>
    </motion.div>
  );
}

// Dashboard cards re-render on every live ticker tick (see
// hooks/use-market-data.ts's applyLiveTicker) — memoize so an update to
// one symbol's price doesn't re-render every other card in the grid.
export const AssetCard = memo(AssetCardImpl);
