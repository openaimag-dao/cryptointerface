"use client";

import { useMemo, useState } from "react";
import { HelpCircle } from "lucide-react";

import { cn } from "@/lib/utils";
import { useAssetTimeline } from "@/hooks/use-asset";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { DirectionBadge } from "@/components/common/direction-badge";
import type { TimelineDataStatus, TimelineEntry } from "@/types";

interface ConfidenceTimelineTabProps {
  baseAsset: string;
  interval?: string;
}

const DATA_STATUS_CLASSNAME: Record<TimelineDataStatus, string> = {
  OK: "border-accent/30 bg-accent-dim text-accent",
  AWAITING_DATA: "border-border-strong bg-white/[0.02] text-muted-foreground opacity-70",
};

function DataStatusBadge({ status }: { status: TimelineDataStatus }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
        DATA_STATUS_CLASSNAME[status],
      )}
    >
      {status === "OK" ? "Explained" : "Awaiting data"}
    </span>
  );
}

function formatTime(unixSeconds: number): string {
  return new Date(unixSeconds * 1000).toLocaleString("en-GB", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  });
}

export function ConfidenceTimelineTab({ baseAsset, interval = "1h" }: ConfidenceTimelineTabProps) {
  const { data: timeline, isLoading } = useAssetTimeline(baseAsset, interval);
  const [selectedEntry, setSelectedEntry] = useState<TimelineEntry | null>(null);

  const entries = useMemo(() => timeline?.entries ?? [], [timeline]);

  if (isLoading || !timeline) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-24 w-full rounded-xl" />
        <Skeleton className="h-24 w-full rounded-xl" />
        <Skeleton className="h-24 w-full rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle>Confidence Timeline</CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          {entries.length === 0 ? (
            <p className="py-6 text-center text-xs text-muted-foreground">
              No recorded decision changes for this symbol/timeframe yet.
            </p>
          ) : (
            <ol className="space-y-3">
              {entries.map((entry, index) => (
                <li
                  key={`${entry.time}-${index}`}
                  className="flex flex-col gap-2 rounded-lg border border-border-subtle p-3 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0 space-y-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-tabular text-xs text-muted-foreground">{formatTime(entry.time)}</span>
                      <DirectionBadge direction={entry.direction} size="sm" />
                      <DataStatusBadge status={entry.dataStatus} />
                    </div>
                    <p className="truncate text-sm text-foreground">
                      {entry.changeSummary ?? `Market Score ${Math.round(entry.score)}, Confidence ${Math.round(entry.confidence)}%`}
                    </p>
                  </div>
                  <Button
                    variant="secondary"
                    size="sm"
                    className="shrink-0"
                    onClick={() => setSelectedEntry(entry)}
                    aria-haspopup="dialog"
                  >
                    <HelpCircle />
                    Почему AI изменил мнение?
                  </Button>
                </li>
              ))}
            </ol>
          )}
        </CardContent>
      </Card>

      <Dialog open={selectedEntry !== null} onOpenChange={(open) => !open && setSelectedEntry(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Explain Decision</DialogTitle>
            <DialogDescription>
              {selectedEntry ? formatTime(selectedEntry.time) : ""}
            </DialogDescription>
          </DialogHeader>
          {selectedEntry ? (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center gap-2">
                <DirectionBadge direction={selectedEntry.direction} size="sm" />
                <span className="font-tabular text-xs text-muted-foreground">
                  Score {Math.round(selectedEntry.score)} · Confidence {Math.round(selectedEntry.confidence)}%
                </span>
                <DataStatusBadge status={selectedEntry.dataStatus} />
              </div>

              <div>
                <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  What changed
                </p>
                <p className="text-sm text-foreground">
                  {selectedEntry.changeSummary ?? "No significant change recorded at this point."}
                </p>
              </div>

              {selectedEntry.dataStatus === "AWAITING_DATA" ? (
                <p className="text-xs text-muted-foreground">
                  This decision was recorded before per-factor reasons were captured — no fabricated
                  explanation is available for it.
                </p>
              ) : (
                <>
                  <div>
                    <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                      Which data influenced this
                    </p>
                    {selectedEntry.reasons && selectedEntry.reasons.length > 0 ? (
                      <ul className="list-disc space-y-1 pl-4 text-sm text-foreground">
                        {selectedEntry.reasons.map((reason, i) => (
                          <li key={i}>{reason}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-muted-foreground">No reasons recorded for this decision.</p>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-accent">Strengthened</p>
                      {selectedEntry.strengthenedFactors.length > 0 ? (
                        <ul className="space-y-1 text-sm text-foreground">
                          {selectedEntry.strengthenedFactors.map((factor) => (
                            <li key={factor}>{factor}</li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-xs text-muted-foreground">None</p>
                      )}
                    </div>
                    <div>
                      <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-danger">Weakened</p>
                      {selectedEntry.weakenedFactors.length > 0 ? (
                        <ul className="space-y-1 text-sm text-foreground">
                          {selectedEntry.weakenedFactors.map((factor) => (
                            <li key={factor}>{factor}</li>
                          ))}
                        </ul>
                      ) : (
                        <p className="text-xs text-muted-foreground">None</p>
                      )}
                    </div>
                  </div>
                </>
              )}
            </div>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}
