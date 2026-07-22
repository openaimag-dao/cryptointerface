import { cn } from "@/lib/utils";
import type { IndicatorStatus, SmartMoneyStatus } from "@/types";

const STATUS_CLASSNAME: Record<IndicatorStatus | SmartMoneyStatus, string> = {
  BULLISH: "border-accent/30 bg-accent-dim text-accent",
  BEARISH: "border-danger/30 bg-danger-dim text-danger",
  NEUTRAL: "border-border-strong bg-white/[0.04] text-muted-foreground",
  OVERBOUGHT: "border-danger/30 bg-danger-dim text-danger",
  OVERSOLD: "border-accent/30 bg-accent-dim text-accent",
  TRENDING: "border-accent/30 bg-accent-dim text-accent",
  RANGING: "border-border-strong bg-white/[0.04] text-muted-foreground",
  TRANSITIONAL: "border-warning/30 bg-warning-dim text-warning",
  HIGH: "border-warning/30 bg-warning-dim text-warning",
  LOW: "border-border-strong bg-white/[0.04] text-muted-foreground",
  MODERATE: "border-warning/30 bg-warning-dim text-warning",
  NOT_YET_IMPLEMENTED: "border-border-strong bg-white/[0.02] text-muted-foreground opacity-60",
};

interface IndicatorStatusBadgeProps {
  status: IndicatorStatus | SmartMoneyStatus;
  className?: string;
}

export function IndicatorStatusBadge({ status, className }: IndicatorStatusBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
        STATUS_CLASSNAME[status],
        className,
      )}
    >
      {status === "NOT_YET_IMPLEMENTED" ? "Not yet implemented" : status.charAt(0) + status.slice(1).toLowerCase()}
    </span>
  );
}
