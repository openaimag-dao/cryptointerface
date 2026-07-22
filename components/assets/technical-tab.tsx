"use client";

import { formatCurrency } from "@/lib/utils";
import { useAssetTechnical } from "@/hooks/use-asset";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { IndicatorStatusBadge } from "@/components/assets/indicator-status-badge";

interface TechnicalTabProps {
  baseAsset: string;
  interval?: string;
}

const BREAKOUT_LABEL: Record<string, string> = {
  BROKEN_ABOVE_RESISTANCE: "Broken above resistance",
  BROKEN_BELOW_SUPPORT: "Broken below support",
  INSIDE_RANGE: "Trading inside range",
};

export function TechnicalTab({ baseAsset, interval = "1h" }: TechnicalTabProps) {
  const { data: technical, isLoading } = useAssetTechnical(baseAsset, interval);

  if (isLoading || !technical) {
    return (
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardContent className="space-y-3 pt-5">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardContent className="space-y-3 pt-5">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle>Structure</CardTitle>
        </CardHeader>
        <CardContent className="grid grid-cols-1 gap-4 pt-0 sm:grid-cols-3">
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground">Nearest Support</span>
            <span className="font-tabular text-sm font-medium text-foreground">
              {technical.nearestSupport !== null ? formatCurrency(technical.nearestSupport) : "—"}
            </span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground">Nearest Resistance</span>
            <span className="font-tabular text-sm font-medium text-foreground">
              {technical.nearestResistance !== null ? formatCurrency(technical.nearestResistance) : "—"}
            </span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground">Breakout Status</span>
            <span className="text-sm font-medium text-foreground">{BREAKOUT_LABEL[technical.breakoutStatus]}</span>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle>Indicators</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            {technical.indicators.map((reading) => (
              <div
                key={reading.name}
                className="flex items-center justify-between gap-3 border-b border-border-subtle py-2.5 last:border-b-0"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-foreground">{reading.name}</p>
                  <p className="truncate text-xs text-muted-foreground">{reading.explanation}</p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <span className="font-tabular text-xs text-muted-foreground">{reading.value}</span>
                  <IndicatorStatusBadge status={reading.status} />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle>Smart Money</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            {technical.smartMoney.map((concept) => (
              <div
                key={concept.name}
                className="flex items-center justify-between gap-3 border-b border-border-subtle py-2.5 last:border-b-0"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-foreground">{concept.name}</p>
                  <p className="truncate text-xs text-muted-foreground">{concept.explanation}</p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  {concept.value ? <span className="font-tabular text-xs text-muted-foreground">{concept.value}</span> : null}
                  <IndicatorStatusBadge status={concept.status} />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
