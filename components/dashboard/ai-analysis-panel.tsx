"use client";

import { motion } from "framer-motion";
import { AlertCircle, Sparkles, TrendingDown, TrendingUp } from "lucide-react";

import { formatCurrency } from "@/lib/utils";
import { useAiDecision } from "@/hooks/use-ai";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { DirectionBadge } from "@/components/common/direction-badge";
import { AiScoreRing } from "@/components/common/ai-score-ring";

interface AiAnalysisPanelProps {
  symbol: string;
}

export function AiAnalysisPanel({ symbol }: AiAnalysisPanelProps) {
  const { data: analysis, isLoading } = useAiDecision(symbol);

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
        {isLoading ? (
          <div className="space-y-4">
            <Skeleton className="h-24 w-full rounded-lg" />
            <Skeleton className="h-32 w-full rounded-lg" />
            <Skeleton className="h-40 w-full rounded-lg" />
          </div>
        ) : !analysis ? (
          <div className="flex h-full flex-col items-center justify-center gap-2 py-12 text-center">
            <AlertCircle className="size-5 text-muted-foreground" />
            <p className="text-xs text-muted-foreground">
              No AI analysis available yet for {symbol}. The Data Engine may still be backfilling history.
            </p>
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
              <AiScoreRing score={Math.round(analysis.marketScore)} size={64} strokeWidth={4} />
              <div>
                <p className="text-xs uppercase tracking-wider text-muted-foreground">Direction</p>
                <div className="mt-1">
                  <DirectionBadge direction={analysis.direction} />
                </div>
                <p className="mt-1.5 font-tabular text-xs text-muted-foreground">
                  Confidence <span className="text-foreground">{Math.round(analysis.confidence)}%</span>
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

            {analysis.risk ? (
              <>
                <div className="space-y-2">
                  <TradeLevelRow label="Entry" value={analysis.risk.entry} tone="default" />
                  <TradeLevelRow label="Stop Loss" value={analysis.risk.stop} tone="negative" />
                  <TradeLevelRow label="Take Profit 1" value={analysis.risk.tp1} tone="positive" />
                  <TradeLevelRow label="Take Profit 2" value={analysis.risk.tp2} tone="positive" />
                  <TradeLevelRow label="Take Profit 3" value={analysis.risk.tp3} tone="positive" />
                </div>

                <Separator />

                <div className="grid grid-cols-3 gap-3">
                  <RiskRewardCell label="RR (TP1)" value={analysis.risk.riskRewardTp1} />
                  <RiskRewardCell label="RR (TP2)" value={analysis.risk.riskRewardTp2} />
                  <RiskRewardCell label="RR (TP3)" value={analysis.risk.riskRewardTp3} />
                </div>
              </>
            ) : (
              <p className="rounded-lg border border-border-subtle bg-white/[0.02] p-3 text-xs text-muted-foreground">
                No trade plan — the engine is in WAIT and isn&apos;t confident enough to propose entry/stop/targets.
              </p>
            )}
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

function RiskRewardCell({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-lg border border-border-subtle bg-white/[0.02] p-3">
      <p className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</p>
      <p className="mt-1 font-tabular text-sm font-semibold text-accent">{value.toFixed(1)}R</p>
    </div>
  );
}
