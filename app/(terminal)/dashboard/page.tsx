"use client";

import { useState } from "react";

import { WATCHLIST_SYMBOLS } from "@/lib/constants";
import { PageHeader } from "@/components/common/page-header";
import { AssetCardGrid } from "@/components/dashboard/asset-card-grid";
import { MarketOverview } from "@/components/dashboard/market-overview";
import { PriceChartPanel } from "@/components/dashboard/price-chart-panel";
import { AiAnalysisPanel } from "@/components/dashboard/ai-analysis-panel";
import { IntelligenceCard } from "@/components/dashboard/intelligence-card";
import { AiExplanationPanel } from "@/components/dashboard/ai-explanation-panel";

export default function DashboardPage() {
  const [symbol, setSymbol] = useState(WATCHLIST_SYMBOLS[0]);

  return (
    <div className="space-y-6">
      <PageHeader title="Dashboard" description="Real-time overview of your watchlist and AI-driven signals" />

      <AssetCardGrid />

      <MarketOverview />

      <IntelligenceCard symbol={symbol} />

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_360px]">
        <PriceChartPanel symbol={symbol} onSymbolChange={setSymbol} />
        <div className="space-y-4">
          <AiAnalysisPanel symbol={symbol} />
          <AiExplanationPanel symbol={symbol} />
        </div>
      </div>
    </div>
  );
}
