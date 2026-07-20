"use client";

import { Percent, Target, TrendingUp, Wallet } from "lucide-react";

import { formatCurrency, formatPercent } from "@/lib/utils";
import { usePortfolio } from "@/hooks/use-portfolio";
import { StatTile } from "@/components/common/stat-tile";
import { Skeleton } from "@/components/ui/skeleton";

export function PortfolioSummary() {
  const { data: portfolio, isLoading } = usePortfolio();

  if (isLoading || !portfolio) {
    return (
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {Array.from({ length: 4 }).map((_, index) => (
          <Skeleton key={index} className="h-[90px] rounded-xl" />
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      <StatTile label="Equity" value={formatCurrency(portfolio.equity)} icon={Wallet} />
      <StatTile
        label="Total PnL"
        value={`${formatCurrency(portfolio.totalPnl)} (${formatPercent(portfolio.totalPnlPercent)})`}
        icon={TrendingUp}
        tone={portfolio.totalPnl >= 0 ? "positive" : "negative"}
      />
      <StatTile label="Win Rate" value={`${portfolio.winRate.toFixed(1)}%`} icon={Percent} tone="positive" />
      <StatTile label="Total Trades" value={String(portfolio.totalTrades)} icon={Target} />
    </div>
  );
}
