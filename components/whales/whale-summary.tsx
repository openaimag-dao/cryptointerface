"use client";

import { ArrowDownToLine, ArrowUpFromLine, Waves } from "lucide-react";

import { formatCompactNumber } from "@/lib/utils";
import { useWhaleTransactions } from "@/hooks/use-whales";
import { StatTile } from "@/components/common/stat-tile";
import { Skeleton } from "@/components/ui/skeleton";

export function WhaleSummary() {
  const { data: transactions, isLoading } = useWhaleTransactions();

  if (isLoading || !transactions) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <Skeleton key={index} className="h-[90px] rounded-xl" />
        ))}
      </div>
    );
  }

  const totalVolume = transactions.reduce((sum, tx) => sum + tx.amountUsd, 0);
  const deposits = transactions.filter((tx) => tx.type === "DEPOSIT").reduce((sum, tx) => sum + tx.amountUsd, 0);
  const withdrawals = transactions
    .filter((tx) => tx.type === "WITHDRAWAL")
    .reduce((sum, tx) => sum + tx.amountUsd, 0);

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <StatTile label="Tracked Volume (24h)" value={`$${formatCompactNumber(totalVolume)}`} icon={Waves} />
      <StatTile
        label="Exchange Deposits"
        value={`$${formatCompactNumber(deposits)}`}
        icon={ArrowDownToLine}
        tone="negative"
      />
      <StatTile
        label="Exchange Withdrawals"
        value={`$${formatCompactNumber(withdrawals)}`}
        icon={ArrowUpFromLine}
        tone="positive"
      />
    </div>
  );
}
