import type { LucideIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import { Card } from "@/components/ui/card";

interface StatTileProps {
  label: string;
  value: string;
  icon?: LucideIcon;
  hint?: string;
  tone?: "default" | "positive" | "negative";
  className?: string;
}

export function StatTile({ label, value, icon: Icon, hint, tone = "default", className }: StatTileProps) {
  return (
    <Card className={cn("p-4", className)}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">{label}</span>
        {Icon ? <Icon className="size-3.5 text-muted-foreground" /> : null}
      </div>
      <p
        className={cn(
          "mt-2 font-tabular text-lg font-semibold tracking-tight",
          tone === "positive" && "text-accent",
          tone === "negative" && "text-danger",
          tone === "default" && "text-foreground",
        )}
      >
        {value}
      </p>
      {hint ? <p className="mt-1 text-xs text-muted-foreground">{hint}</p> : null}
    </Card>
  );
}
