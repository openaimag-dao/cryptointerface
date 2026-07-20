"use client";

import { cn } from "@/lib/utils";
import { useMacroEvents } from "@/hooks/use-macro";
import type { MacroEvent } from "@/types";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";

const IMPACT_VARIANT: Record<MacroEvent["impact"], "danger" | "warning" | "default"> = {
  HIGH: "danger",
  MEDIUM: "warning",
  LOW: "default",
};

export function MacroEventsList() {
  const { data: events, isLoading } = useMacroEvents();

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-foreground">Economic Calendar</CardTitle>
      </CardHeader>
      <div className="px-5 pb-5">
        {isLoading || !events ? (
          <div className="space-y-3">
            {Array.from({ length: 4 }).map((_, index) => (
              <Skeleton key={index} className="h-14 w-full rounded-lg" />
            ))}
          </div>
        ) : (
          <div className="space-y-1">
            {events.map((event, index) => (
              <div key={event.id}>
                {index > 0 ? <Separator className="my-1" /> : null}
                <div className="flex items-center justify-between gap-4 py-2.5">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-foreground">{event.title}</span>
                      <Badge variant={IMPACT_VARIANT[event.impact]}>{event.impact}</Badge>
                    </div>
                    <p className="mt-0.5 text-xs text-muted-foreground">
                      {new Date(event.date).toLocaleDateString("en-US", {
                        weekday: "short",
                        month: "short",
                        day: "numeric",
                      })}
                    </p>
                  </div>
                  <div className={cn("text-right text-xs text-muted-foreground")}>
                    <p>
                      Forecast <span className="text-foreground">{event.forecast}</span>
                    </p>
                    <p>
                      Previous <span className="text-foreground">{event.previous}</span>
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </Card>
  );
}
