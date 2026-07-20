"use client";

import { ArrowRightLeft } from "lucide-react";

import { cn, formatCompactNumber, timeAgo } from "@/lib/utils";
import { useWhaleTransactions } from "@/hooks/use-whales";
import type { WhaleTxType } from "@/types";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";

const TYPE_TONE: Record<WhaleTxType, "accent" | "danger" | "warning" | "default"> = {
  DEPOSIT: "danger",
  WITHDRAWAL: "accent",
  TRANSFER: "default",
  SWAP: "warning",
};

export function WhaleTransactionsTable() {
  const { data: transactions, isLoading } = useWhaleTransactions();

  return (
    <Card className="overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead>Asset</TableHead>
            <TableHead>Type</TableHead>
            <TableHead className="text-right">Amount</TableHead>
            <TableHead className="text-right">Value</TableHead>
            <TableHead>Route</TableHead>
            <TableHead>Exchange</TableHead>
            <TableHead className="text-right">Time</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading || !transactions
            ? Array.from({ length: 8 }).map((_, index) => (
                <TableRow key={index}>
                  {Array.from({ length: 7 }).map((__, cellIndex) => (
                    <TableCell key={cellIndex}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            : transactions.map((tx) => (
                <TableRow key={tx.id}>
                  <TableCell className="font-medium text-foreground">{tx.symbol}</TableCell>
                  <TableCell>
                    <Badge variant={TYPE_TONE[tx.type]}>{tx.type}</Badge>
                  </TableCell>
                  <TableCell className="text-right text-muted-foreground">
                    {formatCompactNumber(tx.amount)} {tx.symbol}
                  </TableCell>
                  <TableCell className="text-right font-medium text-foreground">
                    ${formatCompactNumber(tx.amountUsd)}
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    <span className={cn("inline-flex items-center gap-1.5")}>
                      {tx.from}
                      <ArrowRightLeft className="size-3" />
                      {tx.to}
                    </span>
                  </TableCell>
                  <TableCell className="text-muted-foreground">{tx.exchange ?? "—"}</TableCell>
                  <TableCell className="text-right text-muted-foreground">{timeAgo(tx.timestamp)}</TableCell>
                </TableRow>
              ))}
        </TableBody>
      </Table>
    </Card>
  );
}
