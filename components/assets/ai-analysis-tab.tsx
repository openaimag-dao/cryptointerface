"use client";

import { cn, formatCurrency } from "@/lib/utils";
import { useAssetAnalysis } from "@/hooks/use-asset";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { DirectionBadge } from "@/components/common/direction-badge";
import { IndicatorStatusBadge } from "@/components/assets/indicator-status-badge";
import type { RiskLevel, Scenario } from "@/types";

interface AiAnalysisTabProps {
  baseAsset: string;
  interval?: string;
}

const SCENARIO_STYLE: Record<Scenario["label"], { badge: "BULLISH" | "NEUTRAL" | "BEARISH"; bar: string }> = {
  BULLISH: { badge: "BULLISH", bar: "bg-accent" },
  NEUTRAL: { badge: "NEUTRAL", bar: "bg-warning" },
  BEARISH: { badge: "BEARISH", bar: "bg-danger" },
};

const RISK_LEVEL_STATUS: Record<RiskLevel, "LOW" | "MODERATE" | "HIGH"> = {
  LOW: "LOW",
  MODERATE: "MODERATE",
  HIGH: "HIGH",
  EXTREME: "HIGH",
};

function TradeLevel({ label, value }: { label: string; value: number | null }) {
  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-[10px] uppercase tracking-wider text-muted-foreground">{label}</span>
      <span className="font-tabular text-sm font-medium text-foreground">
        {value !== null ? formatCurrency(value) : "—"}
      </span>
    </div>
  );
}

export function AiAnalysisTab({ baseAsset, interval = "1h" }: AiAnalysisTabProps) {
  const { data: analysis, isLoading } = useAssetAnalysis(baseAsset, interval);

  if (isLoading || !analysis) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-40 w-full rounded-xl" />
        <Skeleton className="h-64 w-full rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="flex-row items-center justify-between space-y-0 pb-3">
          <CardTitle>AI Analysis</CardTitle>
          <DirectionBadge direction={analysis.direction} />
        </CardHeader>
        <CardContent className="pt-0">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div className="flex flex-col gap-0.5">
              <span className="text-[10px] uppercase tracking-wider text-muted-foreground">Market Score</span>
              <span className="font-tabular text-lg font-semibold text-foreground">
                {Math.round(analysis.marketScore)}
              </span>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-[10px] uppercase tracking-wider text-muted-foreground">Confidence</span>
              <span className="font-tabular text-lg font-semibold text-foreground">
                {Math.round(analysis.confidence)}%
              </span>
            </div>
            <TradeLevel label="Entry" value={analysis.entry} />
            <TradeLevel label="Stop" value={analysis.stop} />
            <TradeLevel label="TP1" value={analysis.tp1} />
            <TradeLevel label="TP2" value={analysis.tp2} />
            <TradeLevel label="TP3" value={analysis.tp3} />
            <div className="flex flex-col gap-0.5">
              <span className="text-[10px] uppercase tracking-wider text-muted-foreground">Risk / Reward</span>
              <span className="font-tabular text-sm font-medium text-foreground">
                {analysis.riskReward !== null ? `${analysis.riskReward.toFixed(2)}R` : "—"}
              </span>
            </div>
          </div>

          {analysis.direction === "WAIT" ? (
            <p className="mt-4 text-xs text-muted-foreground">
              No active trade plan — confidence hasn&apos;t cleared the action threshold, so the engine is not
              committing to a direction.
            </p>
          ) : null}

          <ul className="mt-4 space-y-1.5 border-t border-border-subtle pt-4">
            {analysis.reasons.map((reason) => (
              <li key={reason} className="text-xs leading-relaxed text-foreground/80">
                • {reason}
              </li>
            ))}
          </ul>
        </CardContent>
      </Card>

      <div>
        <h3 className="mb-3 text-sm font-medium text-foreground">Scenario Analysis</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {analysis.scenarios.map((scenario) => (
            <Card key={scenario.label}>
              <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
                <IndicatorStatusBadge status={SCENARIO_STYLE[scenario.label].badge} />
                <span className="font-tabular text-sm font-semibold text-foreground">{scenario.probability}%</span>
              </CardHeader>
              <CardContent className="pt-0">
                <Progress value={scenario.probability} indicatorClassName={SCENARIO_STYLE[scenario.label].bar} />
                <ul className="mt-3 space-y-1.5">
                  {scenario.conditions.map((condition) => (
                    <li key={condition} className="text-xs leading-relaxed text-muted-foreground">
                      • {condition}
                    </li>
                  ))}
                </ul>
                {scenario.targets.length > 0 ? (
                  <p className="mt-3 font-tabular text-xs text-foreground">
                    Targets: {scenario.targets.map((t) => formatCurrency(t)).join(" / ")}
                  </p>
                ) : null}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle>Risk Analysis</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-2 gap-4 pt-0 sm:grid-cols-3 lg:grid-cols-6">
          <TradeLevel label="Nearest Support" value={analysis.risk.nearestSupport} />
          <TradeLevel label="Nearest Resistance" value={analysis.risk.nearestResistance} />
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground">ATR Risk</span>
            <span className="font-tabular text-sm font-medium text-foreground">
              {analysis.risk.atrRiskPct !== null ? `${analysis.risk.atrRiskPct.toFixed(2)}%` : "—"}
            </span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground">Volatility Score</span>
            <span className="font-tabular text-sm font-medium text-foreground">
              {Math.round(analysis.risk.volatilityScore)}
            </span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground">Risk Level</span>
            <IndicatorStatusBadge status={RISK_LEVEL_STATUS[analysis.risk.riskLevel]} className="w-fit" />
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground">Max Leverage</span>
            <span className={cn("font-tabular text-sm font-medium text-foreground")}>
              {analysis.risk.maxRecommendedLeverage.toFixed(1)}x
            </span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground">Drawdown Risk</span>
            <span className="font-tabular text-sm font-medium text-foreground">
              {analysis.risk.drawdownRiskPct !== null ? `${analysis.risk.drawdownRiskPct.toFixed(2)}%` : "—"}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
