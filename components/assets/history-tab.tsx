"use client";

import { useMemo } from "react";

import { cn, formatCurrency } from "@/lib/utils";
import { useAssetHistory } from "@/hooks/use-asset";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { DirectionBadge } from "@/components/common/direction-badge";
import { StatTile } from "@/components/common/stat-tile";
import { LineChart } from "@/components/charts/line-chart";
import { CorrelationPanel } from "@/components/assets/correlation-panel";
import type { HistoryPoint, SignalOutcomeStatus } from "@/types";

interface HistoryTabProps {
  baseAsset: string;
  interval?: string;
}

const OUTCOME_CLASSNAME: Record<SignalOutcomeStatus, string> = {
  WIN: "border-accent/30 bg-accent-dim text-accent",
  LOSS: "border-danger/30 bg-danger-dim text-danger",
  OPEN: "border-warning/30 bg-warning-dim text-warning",
  NO_TRADE: "border-border-strong bg-white/[0.04] text-muted-foreground",
};

// lightweight-charts requires strictly increasing, unique timestamps — a
// symbol can have multiple persisted decisions in the same bar, so keep
// only the latest reading per timestamp.
function dedupeByTime(points: HistoryPoint[]): { time: number; value: number }[] {
  const byTime = new Map<number, number>();
  for (const point of points) byTime.set(point.time, point.value);
  return Array.from(byTime.entries())
    .map(([time, value]) => ({ time, value }))
    .sort((a, b) => a.time - b.time);
}

export function HistoryTab({ baseAsset, interval = "1h" }: HistoryTabProps) {
  const { data: history, isLoading } = useAssetHistory(baseAsset, interval);

  const scoreSeries = useMemo(() => dedupeByTime(history?.scoreHistory ?? []), [history]);
  const confidenceSeries = useMemo(() => dedupeByTime(history?.confidenceHistory ?? []), [history]);

  if (isLoading || !history) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-24 w-full rounded-xl" />
        <Skeleton className="h-64 w-full rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatTile
          label="Win Rate"
          value={history.winRate !== null ? `${history.winRate.toFixed(1)}%` : "—"}
          hint="Resolved past signals only"
        />
        <StatTile
          label="Avg Win"
          value={history.avgWinPnlPercent !== null ? `+${history.avgWinPnlPercent.toFixed(2)}%` : "—"}
          tone="positive"
        />
        <StatTile
          label="Avg Loss"
          value={history.avgLossPnlPercent !== null ? `${history.avgLossPnlPercent.toFixed(2)}%` : "—"}
          tone="negative"
        />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle>Decision Score History</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            {scoreSeries.length > 1 ? (
              <LineChart data={scoreSeries} height={220} />
            ) : (
              <p className="py-10 text-center text-xs text-muted-foreground">Not enough history yet.</p>
            )}
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="pb-2">
            <CardTitle>Confidence History</CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            {confidenceSeries.length > 1 ? (
              <LineChart data={confidenceSeries} height={220} color="#38bdf8" />
            ) : (
              <p className="py-10 text-center text-xs text-muted-foreground">Not enough history yet.</p>
            )}
          </CardContent>
        </Card>
      </div>

      <CorrelationPanel baseAsset={baseAsset} interval={interval} />

      <Card className="overflow-hidden">
        <CardHeader className="pb-2">
          <CardTitle>Recent Signals</CardTitle>
        </CardHeader>
        <CardContent className="pt-0">
          {history.signals.length === 0 ? (
            <p className="py-6 text-center text-xs text-muted-foreground">No signals recorded for this symbol yet.</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead>Time</TableHead>
                  <TableHead>Direction</TableHead>
                  <TableHead className="text-right">Score</TableHead>
                  <TableHead className="text-right">Confidence</TableHead>
                  <TableHead className="text-right">Entry</TableHead>
                  <TableHead className="text-right">Stop</TableHead>
                  <TableHead className="text-right">TP1</TableHead>
                  <TableHead className="text-right">Outcome</TableHead>
                  <TableHead className="text-right">P&amp;L</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {history.signals.map((signal, index) => (
                  <TableRow key={`${signal.time}-${index}`}>
                    <TableCell className="text-xs text-muted-foreground">
                      {new Date(signal.time * 1000).toLocaleString("en-GB", {
                        dateStyle: "medium",
                        timeStyle: "short",
                        timeZone: "UTC",
                      })}
                    </TableCell>
                    <TableCell>
                      <DirectionBadge direction={signal.direction} size="sm" />
                    </TableCell>
                    <TableCell className="text-right font-tabular">{Math.round(signal.score)}</TableCell>
                    <TableCell className="text-right font-tabular">{Math.round(signal.confidence)}%</TableCell>
                    <TableCell className="text-right font-tabular">
                      {signal.entry !== null ? formatCurrency(signal.entry) : "—"}
                    </TableCell>
                    <TableCell className="text-right font-tabular">
                      {signal.stop !== null ? formatCurrency(signal.stop) : "—"}
                    </TableCell>
                    <TableCell className="text-right font-tabular">
                      {signal.tp1 !== null ? formatCurrency(signal.tp1) : "—"}
                    </TableCell>
                    <TableCell className="text-right">
                      <span
                        className={cn(
                          "inline-flex items-center rounded-md border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wider",
                          OUTCOME_CLASSNAME[signal.outcome],
                        )}
                      >
                        {signal.outcome.replace("_", " ")}
                      </span>
                    </TableCell>
                    <TableCell
                      className={cn(
                        "text-right font-tabular",
                        signal.pnlPercent !== null && (signal.pnlPercent >= 0 ? "text-accent" : "text-danger"),
                      )}
                    >
                      {signal.pnlPercent !== null
                        ? `${signal.pnlPercent >= 0 ? "+" : ""}${signal.pnlPercent.toFixed(2)}%`
                        : "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
