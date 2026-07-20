"use client";

import { cn } from "@/lib/utils";
import { useMacroIndicators } from "@/hooks/use-macro";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function MacroIndicatorsGrid() {
  const { data: indicators, isLoading } = useMacroIndicators();

  if (isLoading || !indicators) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} className="h-[120px] rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {indicators.map((indicator) => (
        <Card key={indicator.id} className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              {indicator.label}
            </span>
            <span
              className={cn(
                "font-tabular text-xs font-medium",
                indicator.sentiment === "POSITIVE" && "text-accent",
                indicator.sentiment === "NEGATIVE" && "text-danger",
                indicator.sentiment === "NEUTRAL" && "text-muted-foreground",
              )}
            >
              {indicator.changeLabel}
            </span>
          </div>
          <p className="mt-2 font-tabular text-2xl font-semibold text-foreground">{indicator.value}</p>
          <p className="mt-1.5 text-xs leading-relaxed text-muted-foreground">{indicator.description}</p>
        </Card>
      ))}
    </div>
  );
}
