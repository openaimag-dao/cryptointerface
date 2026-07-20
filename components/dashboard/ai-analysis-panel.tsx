"use client";

import { motion } from "framer-motion";
import { Sparkles, TrendingDown, TrendingUp } from "lucide-react";

import { formatCurrency } from "@/lib/utils";
import { useAiAnalysis } from "@/hooks/use-signals";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { DirectionBadge } from "@/components/common/direction-badge";
import { AiScoreRing } from "@/components/common/ai-score-ring";

interface AiAnalysisPanelProps {
  symbol: string;
}

export function AiAnalysisPanel({ symbol }: AiAnalysisPanelProps) {
  const { data: analysis, isLoading } = useAiAnalysis(symbol);

  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-1.5 text-foreground">
          <Sparkles className="size-4 text-accent" />
          AI Analysis
        </CardTitle>
        <span className="text-xs text-muted-foreground">{symbol}</span>
      </CardHeader>

      <CardContent className="flex-1">
        {isLoading || !analysis ? (
          <div className="space-y-4">
            <Skeleton className="h-24 w-full rounded-lg" />
            <Skeleton className="h-32 w-full rounded-lg" />
            <Skeleton className="h-40 w-full rounded-lg" />
          </div>
        ) : (
          <motion.div
            key={symbol}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.25 }}
            className="space-y-5"
          >
            <div className="flex items-center gap-4 rounded-lg border border-border-subtle bg-white/[0.02] p-4">
              <AiScoreRing score={analysis.aiScore} size={64} strokeWidth={4} />
              <div>
                <p className="text-xs uppercase tracking-wider text-muted-foreground">Direction</p>
                <div className="mt-1">
                  <DirectionBadge direction={analysis.direction} />
                </div>
                <p className="mt-1.5 font-tabular text-xs text-muted-foreground">
                  Confidence <span className="text-foreground">{analysis.confidence}%</span>
                </p>
              </div>
            </div>

            <div>
              <p className="mb-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">Reasoning</p>
              <ul className="space-y-2">
                {analysis.reasons.map((reason) => (
                  <li key={reason} className="flex items-start gap-2 text-xs leading-relaxed text-foreground/90">
                    {analysis.direction === "SHORT" ? (
                      <TrendingDown className="mt-0.5 size-3.5 shrink-0 text-danger" />
                    ) : (
                      <TrendingUp className="mt-0.5 size-3.5 shrink-0 text-accent" />
                    )}
                    {reason}
                  </li>
                ))}
              </ul>
            </div>

            <Separator />

            <div className="space-y-2">
              <TradeLevelRow label="Entry" value={analysis.entry} tone="default" />
              <TradeLevelRow label="Stop Loss" value={analysis.stopLoss} tone="negative" />
              <TradeLevelRow label="Take Profit 1" value={analysis.takeProfit1} tone="positive" />
              <TradeLevelRow label="Take Profit 2" value={analysis.takeProfit2} tone="positive" />
              <TradeLevelRow label="Take Profit 3" value={analysis.takeProfit3} tone="positive" />
            </div>

            <Separator />

            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg border border-border-subtle bg-white/[0.02] p-3">
                <p className="text-[10px] uppercase tracking-wider text-muted-foreground">Risk</p>
                <p className="mt-1 font-tabular text-sm font-semibold text-danger">{formatCurrency(analysis.risk)}</p>
              </div>
              <div className="rounded-lg border border-border-subtle bg-white/[0.02] p-3">
                <p className="text-[10px] uppercase tracking-wider text-muted-foreground">Reward</p>
                <p className="mt-1 font-tabular text-sm font-semibold text-accent">{formatCurrency(analysis.reward)}</p>
              </div>
            </div>
          </motion.div>
        )}
      </CardContent>
    </Card>
  );
}

function TradeLevelRow({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "default" | "positive" | "negative";
}) {
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-muted-foreground">{label}</span>
      <span
        className={
          tone === "positive"
            ? "font-tabular font-medium text-accent"
            : tone === "negative"
              ? "font-tabular font-medium text-danger"
              : "font-tabular font-medium text-foreground"
        }
      >
        {formatCurrency(value)}
      </span>
    </div>
  );
}
