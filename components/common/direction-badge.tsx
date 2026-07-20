import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";

import { cn } from "@/lib/utils";
import type { Direction } from "@/types";

const DIRECTION_CONFIG: Record<Direction, { label: string; className: string; Icon: typeof ArrowUpRight }> = {
  LONG: {
    label: "LONG",
    className: "border-accent/30 bg-accent-dim text-accent",
    Icon: ArrowUpRight,
  },
  SHORT: {
    label: "SHORT",
    className: "border-danger/30 bg-danger-dim text-danger",
    Icon: ArrowDownRight,
  },
  WAIT: {
    label: "WAIT",
    className: "border-warning/30 bg-warning-dim text-warning",
    Icon: Minus,
  },
};

interface DirectionBadgeProps {
  direction: Direction;
  className?: string;
  size?: "sm" | "md";
}

export function DirectionBadge({ direction, className, size = "md" }: DirectionBadgeProps) {
  const { label, className: colorClassName, Icon } = DIRECTION_CONFIG[direction];

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md border font-semibold tracking-wide",
        size === "sm" ? "px-1.5 py-0.5 text-[10px]" : "px-2 py-1 text-xs",
        colorClassName,
        className,
      )}
    >
      <Icon className={size === "sm" ? "size-2.5" : "size-3"} />
      {label}
    </span>
  );
}
