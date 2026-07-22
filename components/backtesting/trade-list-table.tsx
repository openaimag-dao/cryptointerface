"use client";

import { Download } from "lucide-react";

import { reportToJson, tradesToCsv } from "@/lib/backtest-export";
import { downloadTextFile } from "@/lib/download";
import { cn, formatCompactNumber, formatPercent } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import type { BacktestReport, BacktestTrade } from "@/types";

function formatDate(unixSeconds: number): string {
  return new Date(unixSeconds * 1000).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    timeZone: "UTC",
  });
}

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  if (hours < 24) return `${hours}h`;
  return `${Math.floor(hours / 24)}d ${hours % 24}h`;
}

const REASON_LABEL: Record<BacktestTrade["exitReason"], string> = {
  TP1: "Take Profit",
  SL: "Stop Loss",
  END_OF_DATA: "End of Data",
};

export function TradeListTable({ report, trades }: { report: BacktestReport; trades: BacktestTrade[] }) {
  function handleExportCsv() {
    downloadTextFile(`backtest-${report.run.id}-trades.csv`, tradesToCsv(trades), "text/csv");
  }

  function handleExportJson() {
    downloadTextFile(`backtest-${report.run.id}-report.json`, reportToJson(report, trades), "application/json");
  }

  return (
    <Card className="overflow-hidden">
      <div className="flex items-center justify-between border-b border-border-subtle px-4 py-3">
        <h3 className="text-sm font-medium text-foreground">Trade List ({trades.length})</h3>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="gap-1.5" onClick={handleExportCsv}>
            <Download className="size-3.5" />
            CSV
          </Button>
          <Button variant="outline" size="sm" className="gap-1.5" onClick={handleExportJson}>
            <Download className="size-3.5" />
            JSON
          </Button>
        </div>
      </div>
      <div className="max-h-[480px] overflow-auto">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead>Date</TableHead>
              <TableHead>Coin</TableHead>
              <TableHead>Direction</TableHead>
              <TableHead className="text-right">Entry</TableHead>
              <TableHead className="text-right">Exit</TableHead>
              <TableHead className="text-right">PnL</TableHead>
              <TableHead className="text-right">Duration</TableHead>
              <TableHead>Reason</TableHead>
              <TableHead className="text-right">Score</TableHead>
              <TableHead className="text-right">Confidence</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {trades.length === 0 ? (
              <TableRow>
                <TableCell colSpan={10} className="py-8 text-center text-sm text-muted-foreground">
                  No trades were opened during this run.
                </TableCell>
              </TableRow>
            ) : (
              trades.map((trade) => (
                <TableRow key={trade.id}>
                  <TableCell className="text-muted-foreground">{formatDate(trade.entryTime)}</TableCell>
                  <TableCell className="font-medium text-foreground">{trade.symbol}</TableCell>
                  <TableCell>
                    <Badge variant={trade.direction === "LONG" ? "accent" : "danger"}>{trade.direction}</Badge>
                  </TableCell>
                  <TableCell className="text-right text-muted-foreground">
                    ${formatCompactNumber(trade.entryPrice)}
                  </TableCell>
                  <TableCell className="text-right text-muted-foreground">
                    ${formatCompactNumber(trade.exitPrice)}
                  </TableCell>
                  <TableCell
                    className={cn(
                      "text-right font-medium",
                      trade.pnl >= 0 ? "text-accent" : "text-danger",
                    )}
                  >
                    ${formatCompactNumber(trade.pnl)} ({formatPercent(trade.pnlPercent)})
                  </TableCell>
                  <TableCell className="text-right text-muted-foreground">
                    {formatDuration(trade.durationSeconds)}
                  </TableCell>
                  <TableCell className="text-muted-foreground">{REASON_LABEL[trade.exitReason]}</TableCell>
                  <TableCell className="text-right text-muted-foreground">{trade.decisionScore.toFixed(0)}</TableCell>
                  <TableCell className="text-right text-muted-foreground">{trade.confidence.toFixed(0)}%</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </div>
    </Card>
  );
}
