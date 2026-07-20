"use client";

import { motion } from "framer-motion";
import { Clock, Sparkles } from "lucide-react";

import { cn, formatCurrency, timeAgo } from "@/lib/utils";
import type { AiSignal } from "@/types";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { DirectionBadge } from "@/components/common/direction-badge";

interface SignalCardProps {
  signal: AiSignal;
  index?: number;
}

export function SignalCard({ signal, index = 0 }: SignalCardProps) {
  const accentGlow =
    signal.direction === "LONG"
      ? "hover:shadow-[0_0_0_1px_rgba(0,230,118,0.25),0_20px_40px_-20px_rgba(0,230,118,0.3)]"
      : signal.direction === "SHORT"
        ? "hover:shadow-[0_0_0_1px_rgba(255,59,92,0.25),0_20px_40px_-20px_rgba(255,59,92,0.3)]"
        : "hover:shadow-[0_0_0_1px_rgba(255,176,32,0.25),0_20px_40px_-20px_rgba(255,176,32,0.3)]";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.04 }}
    >
      <Card className={cn("h-full transition-shadow duration-300", accentGlow)}>
        <CardHeader className="flex-row items-start justify-between space-y-0 pb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-base font-semibold text-foreground">{signal.symbol}</span>
              <Badge variant="outline">{signal.timeframe}</Badge>
            </div>
            <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="size-3" />
              {timeAgo(signal.createdAt)}
            </p>
          </div>
          <DirectionBadge direction={signal.direction} />
        </CardHeader>

        <CardContent className="space-y-4 pt-0">
          <div className="flex items-center gap-2 rounded-lg border border-border-subtle bg-white/[0.02] px-3 py-2">
            <Sparkles className="size-4 text-accent" />
            <span className="text-xs text-muted-foreground">Confidence</span>
            <span className="ml-auto font-tabular text-sm font-semibold text-accent">{signal.confidence}%</span>
          </div>

          <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs">
            <LevelItem label="Entry" value={signal.entry} />
            <LevelItem label="Stop" value={signal.stopLoss} tone="negative" />
            <LevelItem label="TP1" value={signal.takeProfit1} tone="positive" />
            <LevelItem label="TP2" value={signal.takeProfit2} tone="positive" />
            <LevelItem label="TP3" value={signal.takeProfit3} tone="positive" />
            <LevelItem label="R:R" value={signal.riskReward} isRatio />
          </div>

          <Separator />

          <div>
            <p className="mb-1.5 text-xs font-medium uppercase tracking-wider text-muted-foreground">Reasons</p>
            <ul className="space-y-1.5">
              {signal.reasons.map((reason) => (
                <li key={reason} className="flex gap-2 text-xs leading-relaxed text-foreground/90">
                  <span className="mt-1.5 size-1 shrink-0 rounded-full bg-accent" />
                  {reason}
                </li>
              ))}
            </ul>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function LevelItem({
  label,
  value,
  tone = "default",
  isRatio = false,
}: {
  label: string;
  value: number;
  tone?: "default" | "positive" | "negative";
  isRatio?: boolean;
}) {
  return (
    <div className="flex items-center justify-between rounded-md bg-white/[0.02] px-2 py-1.5">
      <span className="text-muted-foreground">{label}</span>
      <span
        className={cn(
          "font-tabular font-medium",
          tone === "positive" && "text-accent",
          tone === "negative" && "text-danger",
          tone === "default" && "text-foreground",
        )}
      >
        {isRatio ? `${value.toFixed(1)}x` : formatCurrency(value)}
      </span>
    </div>
  );
}
