"use client";

import { ArrowDownToLine, ArrowUpFromLine } from "lucide-react";

import { formatCompactNumber, timeAgo } from "@/lib/utils";
import { useAssetWhales } from "@/hooks/use-asset";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import type { WhaleDirection } from "@/types";

interface WhalesTabProps {
  baseAsset: string;
}

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

export function WhalesTab({ baseAsset }: WhalesTabProps) {
  const { data: whales, isLoading } = useAssetWhales(baseAsset);

  if (isLoading || !whales) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-24 w-full rounded-xl" />
        <Skeleton className="h-64 w-full rounded-xl" />
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="grid grid-cols-1 gap-4 pt-5 sm:grid-cols-3">
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground">Whale Score</span>
            <span className="font-tabular text-lg font-semibold text-foreground">
              {Math.round(whales.whaleScore)}
            </span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground">To Exchange (24h)</span>
            <span className="font-tabular text-lg font-semibold text-danger">
              ${formatCompactNumber(whales.toExchangeUsd24h)}
            </span>
          </div>
          <div className="flex flex-col gap-0.5">
            <span className="text-[10px] uppercase tracking-wider text-muted-foreground">From Exchange (24h)</span>
            <span className="font-tabular text-lg font-semibold text-accent">
              ${formatCompactNumber(whales.fromExchangeUsd24h)}
            </span>
          </div>
        </CardContent>
      </Card>

      <Card className="overflow-hidden">
        <CardHeader className="pb-2">
          <CardTitle>Recent Events</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {whales.events.length === 0 ? (
            <p className="px-5 pb-5 text-xs text-muted-foreground">No tracked whale activity for this asset yet.</p>
          ) : (
            <div className="max-h-[420px] overflow-y-auto">
              <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead>Direction</TableHead>
                  <TableHead className="text-right">Amount</TableHead>
                  <TableHead className="text-right">Value</TableHead>
                  <TableHead>Exchange</TableHead>
                  <TableHead>Route</TableHead>
                  <TableHead className="text-right">Time</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {whales.events.map((tx) => (
                  <TableRow key={tx.id}>
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
                      {truncateAddress(tx.fromAddress)} → {truncateAddress(tx.toAddress)}
                    </TableCell>
                    <TableCell className="text-right text-muted-foreground">{timeAgo(tx.timestamp)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
