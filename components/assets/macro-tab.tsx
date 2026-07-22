"use client";

import { cn, formatPercent } from "@/lib/utils";
import { useAssetMacro } from "@/hooks/use-asset";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

interface MacroTabProps {
  baseAsset: string;
}

export function MacroTab({ baseAsset }: MacroTabProps) {
  const { data: readings, isLoading } = useAssetMacro(baseAsset);

  if (isLoading || !readings) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} className="h-[110px] rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {readings.map((reading) => (
        <Card key={reading.id} className="p-5">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
              {reading.label}
            </span>
            <span
              className={cn(
                "rounded-md border px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
                reading.influence === "HIGH"
                  ? "border-warning/30 bg-warning-dim text-warning"
                  : "border-border-strong bg-white/[0.04] text-muted-foreground",
              )}
            >
              {reading.influence} influence
            </span>
          </div>
          <p className="mt-2 font-tabular text-2xl font-semibold text-foreground">
            {reading.current !== null ? reading.current.toLocaleString(undefined, { maximumFractionDigits: 2 }) : "—"}
          </p>
          <p
            className={cn(
              "mt-1.5 text-xs font-medium",
              reading.trend === "UP" && "text-accent",
              reading.trend === "DOWN" && "text-danger",
              reading.trend === "NEUTRAL" && "text-muted-foreground",
            )}
          >
            {reading.changePercent !== null ? formatPercent(reading.changePercent) : "No change data yet"}
          </p>
        </Card>
      ))}
    </div>
  );
}
