"use client";

import { motion } from "framer-motion";

import { cn, formatCompactNumber, formatCurrency, formatPercent } from "@/lib/utils";
import type { AssetQuote } from "@/types";
import { Card } from "@/components/ui/card";
import { DirectionBadge } from "@/components/common/direction-badge";
import { AiScoreRing } from "@/components/common/ai-score-ring";

interface AssetCardProps {
  asset: AssetQuote;
  index?: number;
}

export function AssetCard({ asset, index = 0 }: AssetCardProps) {
  const isUp = asset.changePercent24h >= 0;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
    >
      <Card className="group relative overflow-hidden p-5 transition-colors hover:border-border-strong">
        <div
          className={cn(
            "pointer-events-none absolute inset-x-0 top-0 h-24 opacity-0 transition-opacity duration-300 group-hover:opacity-100",
            isUp ? "bg-gradient-to-b from-accent/10 to-transparent" : "bg-gradient-to-b from-danger/10 to-transparent",
          )}
        />

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
