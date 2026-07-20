"use client";

import { formatCurrency } from "@/lib/utils";
import { useLiquidationHeatmap } from "@/hooks/use-liquidations";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export function LiquidationHeatmap() {
  const { data: cells, isLoading } = useLiquidationHeatmap();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-foreground">Liquidation Heatmap · BTCUSDT</CardTitle>
      </CardHeader>
      <div className="flex h-40 items-end gap-[3px] px-5 pb-5">
        {isLoading || !cells
          ? Array.from({ length: 40 }).map((_, index) => (
              <Skeleton key={index} className="flex-1" style={{ height: `${20 + (index % 7) * 10}%` }} />
            ))
          : cells.map((cell) => (
              <Tooltip key={cell.price}>
                <TooltipTrigger asChild>
                  <div
                    className="flex-1 rounded-t-sm transition-[height] duration-300"
                    style={{
                      height: `${Math.max(6, cell.intensity * 100)}%`,
                      background: `color-mix(in srgb, var(--accent) ${Math.round(cell.intensity * 100)}%, var(--danger))`,
                      opacity: 0.35 + cell.intensity * 0.65,
                    }}
                  />
                </TooltipTrigger>
                <TooltipContent>{formatCurrency(cell.price)}</TooltipContent>
              </Tooltip>
            ))}
      </div>
    </Card>
  );
}
