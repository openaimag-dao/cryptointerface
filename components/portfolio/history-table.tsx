"use client";

import { cn, formatCurrency, formatPercent, timeAgo } from "@/lib/utils";
import { usePortfolio } from "@/hooks/use-portfolio";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { DirectionBadge } from "@/components/common/direction-badge";

export function HistoryTable() {
  const { data: portfolio, isLoading } = usePortfolio();

  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <CardTitle className="text-foreground">Trade History</CardTitle>
      </CardHeader>
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead>Symbol</TableHead>
            <TableHead>Direction</TableHead>
            <TableHead className="text-right">Entry</TableHead>
            <TableHead className="text-right">Exit</TableHead>
            <TableHead className="text-right">PnL</TableHead>
            <TableHead className="text-right">Closed</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading || !portfolio
            ? Array.from({ length: 4 }).map((_, index) => (
                <TableRow key={index}>
                  {Array.from({ length: 6 }).map((__, cellIndex) => (
                    <TableCell key={cellIndex}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            : portfolio.history.map((trade) => (
                <TableRow key={trade.id}>
                  <TableCell className="font-medium text-foreground">{trade.symbol}</TableCell>
                  <TableCell>
                    <DirectionBadge direction={trade.direction} size="sm" />
                  </TableCell>
                  <TableCell className="text-right">{formatCurrency(trade.entryPrice)}</TableCell>
                  <TableCell className="text-right">{formatCurrency(trade.exitPrice)}</TableCell>
                  <TableCell className={cn("text-right", trade.pnl >= 0 ? "text-accent" : "text-danger")}>
                    {formatCurrency(trade.pnl)}
                    <span className="ml-1 text-xs opacity-80">({formatPercent(trade.pnlPercent)})</span>
                  </TableCell>
                  <TableCell className="text-right text-muted-foreground">{timeAgo(trade.closedAt)}</TableCell>
                </TableRow>
              ))}
        </TableBody>
      </Table>
    </Card>
  );
}
