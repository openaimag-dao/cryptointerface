"use client";

import { useState } from "react";

import { WATCHLIST_SYMBOLS } from "@/lib/mock/assets";
import { PageHeader } from "@/components/common/page-header";
import { AssetCardGrid } from "@/components/dashboard/asset-card-grid";
import { MarketOverview } from "@/components/dashboard/market-overview";
import { PriceChartPanel } from "@/components/dashboard/price-chart-panel";
import { AiAnalysisPanel } from "@/components/dashboard/ai-analysis-panel";

export default function DashboardPage() {
  const [symbol, setSymbol] = useState(WATCHLIST_SYMBOLS[0]);

  return (
    <div className="space-y-6">
      <PageHeader title="Dashboard" description="Real-time overview of your watchlist and AI-driven signals" />

      <AssetCardGrid />

      <MarketOverview />

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_360px]">
        <PriceChartPanel symbol={symbol} onSymbolChange={setSymbol} />
        <AiAnalysisPanel symbol={symbol} />
      </div>
    </div>
  );
}
