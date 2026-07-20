"use client";

import { cn, formatCurrency, formatPercent } from "@/lib/utils";
import { usePortfolio } from "@/hooks/use-portfolio";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { DirectionBadge } from "@/components/common/direction-badge";

export function PositionsTable() {
  const { data: portfolio, isLoading } = usePortfolio();

  return (
    <Card className="overflow-hidden">
      <CardHeader>
        <CardTitle className="text-foreground">Open Positions</CardTitle>
      </CardHeader>
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead>Symbol</TableHead>
            <TableHead>Direction</TableHead>
            <TableHead className="text-right">Size</TableHead>
            <TableHead className="text-right">Entry</TableHead>
            <TableHead className="text-right">Mark</TableHead>
            <TableHead className="text-right">Leverage</TableHead>
            <TableHead className="text-right">PnL</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading || !portfolio
            ? Array.from({ length: 3 }).map((_, index) => (
                <TableRow key={index}>
                  {Array.from({ length: 7 }).map((__, cellIndex) => (
                    <TableCell key={cellIndex}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            : portfolio.openPositions.map((position) => (
                <TableRow key={position.id}>
                  <TableCell className="font-medium text-foreground">{position.symbol}</TableCell>
                  <TableCell>
                    <DirectionBadge direction={position.direction} size="sm" />
                  </TableCell>
                  <TableCell className="text-right text-muted-foreground">{position.size}</TableCell>
                  <TableCell className="text-right">{formatCurrency(position.entryPrice)}</TableCell>
                  <TableCell className="text-right">{formatCurrency(position.markPrice)}</TableCell>
                  <TableCell className="text-right text-muted-foreground">{position.leverage}x</TableCell>
                  <TableCell className={cn("text-right", position.pnl >= 0 ? "text-accent" : "text-danger")}>
                    {formatCurrency(position.pnl)}
                    <span className="ml-1 text-xs opacity-80">({formatPercent(position.pnlPercent)})</span>
                  </TableCell>
                </TableRow>
              ))}
        </TableBody>
      </Table>
    </Card>
  );
}
