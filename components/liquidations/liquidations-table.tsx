"use client";

import { cn, formatCompactNumber, formatCurrency, timeAgo } from "@/lib/utils";
import { useLiquidations } from "@/hooks/use-liquidations";
import { Card } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { DirectionBadge } from "@/components/common/direction-badge";

export function LiquidationsTable() {
  const { data: liquidations, isLoading } = useLiquidations();

  return (
    <Card className="overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead>Symbol</TableHead>
            <TableHead>Side</TableHead>
            <TableHead className="text-right">Price</TableHead>
            <TableHead className="text-right">Value</TableHead>
            <TableHead>Exchange</TableHead>
            <TableHead className="text-right">Time</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading || !liquidations
            ? Array.from({ length: 8 }).map((_, index) => (
                <TableRow key={index}>
                  {Array.from({ length: 6 }).map((__, cellIndex) => (
                    <TableCell key={cellIndex}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            : liquidations.map((event) => (
                <TableRow key={event.id}>
                  <TableCell className="font-medium text-foreground">{event.symbol}</TableCell>
                  <TableCell>
                    <DirectionBadge direction={event.side} size="sm" />
                  </TableCell>
                  <TableCell className="text-right">{formatCurrency(event.price)}</TableCell>
                  <TableCell
                    className={cn(
                      "text-right font-medium",
                      event.side === "LONG" ? "text-danger" : "text-accent",
                    )}
                  >
                    ${formatCompactNumber(event.amountUsd)}
                  </TableCell>
                  <TableCell className="text-muted-foreground">{event.exchange}</TableCell>
                  <TableCell className="text-right text-muted-foreground">{timeAgo(event.timestamp)}</TableCell>
                </TableRow>
              ))}
        </TableBody>
      </Table>
    </Card>
  );
}
