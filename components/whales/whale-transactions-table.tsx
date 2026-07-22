"use client";

import { ArrowDownToLine, ArrowRightLeft, ArrowUpFromLine } from "lucide-react";

import { formatCompactNumber, timeAgo } from "@/lib/utils";
import { useWhaleTransactions } from "@/hooks/use-whales";
import type { WhaleDirection } from "@/types";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";

const DIRECTION_TONE: Record<WhaleDirection, "danger" | "accent"> = {
  TO_EXCHANGE: "danger",
  FROM_EXCHANGE: "accent",
};

const DIRECTION_LABEL: Record<WhaleDirection, string> = {
  TO_EXCHANGE: "To Exchange",
  FROM_EXCHANGE: "From Exchange",
};

function truncateAddress(address: string): string {
  return `${address.slice(0, 6)}…${address.slice(-4)}`;
}

export function WhaleTransactionsTable() {
  const { data: transactions, isLoading } = useWhaleTransactions();

  return (
    <Card className="overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead>Asset</TableHead>
            <TableHead>Direction</TableHead>
            <TableHead className="text-right">Amount</TableHead>
            <TableHead className="text-right">Value</TableHead>
            <TableHead>Exchange</TableHead>
            <TableHead>Route</TableHead>
            <TableHead className="text-right">Confidence</TableHead>
            <TableHead className="text-right">Time</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {isLoading || !transactions
            ? Array.from({ length: 8 }).map((_, index) => (
                <TableRow key={index}>
                  {Array.from({ length: 8 }).map((__, cellIndex) => (
                    <TableCell key={cellIndex}>
                      <Skeleton className="h-4 w-full" />
                    </TableCell>
                  ))}
                </TableRow>
              ))
            : transactions.map((tx) => (
                <TableRow key={tx.id}>
                  <TableCell className="font-medium text-foreground">{tx.asset}</TableCell>
                  <TableCell>
                    <Badge variant={DIRECTION_TONE[tx.direction]} className="inline-flex items-center gap-1">
                      {tx.direction === "TO_EXCHANGE" ? (
                        <ArrowDownToLine className="size-3" />
                      ) : (
                        <ArrowUpFromLine className="size-3" />
                      )}
                      {DIRECTION_LABEL[tx.direction]}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-right text-muted-foreground">
                    {formatCompactNumber(tx.amount)} {tx.asset}
                  </TableCell>
                  <TableCell className="text-right font-medium text-foreground">
                    ${formatCompactNumber(tx.usdValue)}
                  </TableCell>
                  <TableCell className="text-muted-foreground">{tx.exchange ?? "—"}</TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    <span className="inline-flex items-center gap-1.5">
                      {truncateAddress(tx.fromAddress)}
                      <ArrowRightLeft className="size-3" />
                      {truncateAddress(tx.toAddress)}
                    </span>
                  </TableCell>
                  <TableCell className="text-right text-muted-foreground">{tx.confidence.toFixed(0)}%</TableCell>
                  <TableCell className="text-right text-muted-foreground">{timeAgo(tx.timestamp)}</TableCell>
                </TableRow>
              ))}
        </TableBody>
      </Table>
    </Card>
  );
}
