"use client";

import { useMemo, useState } from "react";
import { useParams } from "next/navigation";
import dynamic from "next/dynamic";

import { PageHeader } from "@/components/common/page-header";
import { AssetTopBar } from "@/components/assets/asset-top-bar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";

const OverviewTab = dynamic(() => import("@/components/assets/overview-tab").then((m) => m.OverviewTab), {
  loading: () => <Skeleton className="h-[420px] w-full rounded-lg" />,
});
const TechnicalTab = dynamic(() => import("@/components/assets/technical-tab").then((m) => m.TechnicalTab), {
  loading: () => <Skeleton className="h-[420px] w-full rounded-lg" />,
});
const DerivativesTab = dynamic(() => import("@/components/assets/derivatives-tab").then((m) => m.DerivativesTab), {
  loading: () => <Skeleton className="h-[420px] w-full rounded-lg" />,
});
const WhalesTab = dynamic(() => import("@/components/assets/whales-tab").then((m) => m.WhalesTab), {
  loading: () => <Skeleton className="h-[420px] w-full rounded-lg" />,
});
const NewsTab = dynamic(() => import("@/components/assets/news-tab").then((m) => m.NewsTab), {
  loading: () => <Skeleton className="h-[420px] w-full rounded-lg" />,
});
const MacroTab = dynamic(() => import("@/components/assets/macro-tab").then((m) => m.MacroTab), {
  loading: () => <Skeleton className="h-[420px] w-full rounded-lg" />,
});
const SentimentTab = dynamic(() => import("@/components/assets/sentiment-tab").then((m) => m.SentimentTab), {
  loading: () => <Skeleton className="h-[420px] w-full rounded-lg" />,
});
const AiAnalysisTab = dynamic(() => import("@/components/assets/ai-analysis-tab").then((m) => m.AiAnalysisTab), {
  loading: () => <Skeleton className="h-[420px] w-full rounded-lg" />,
});
const HistoryTab = dynamic(() => import("@/components/assets/history-tab").then((m) => m.HistoryTab), {
  loading: () => <Skeleton className="h-[420px] w-full rounded-lg" />,
});

const TAB_ITEMS = [
  { value: "overview", label: "Overview" },
  { value: "technical", label: "Technical" },
  { value: "derivatives", label: "Derivatives" },
  { value: "whales", label: "Whales" },
  { value: "news", label: "News" },
  { value: "macro", label: "Macro" },
  { value: "sentiment", label: "Sentiment" },
  { value: "ai-analysis", label: "AI Analysis" },
  { value: "history", label: "History" },
] as const;

export default function AssetDetailPage() {
  const params = useParams<{ symbol: string }>();
  const baseAsset = useMemo(() => (params.symbol ?? "").toUpperCase(), [params.symbol]);
  const tradingPair = `${baseAsset}USDT`;
  const [tab, setTab] = useState<string>("overview");

  if (!baseAsset) {
    return null;
  }

  return (
    <div className="space-y-6">
      <PageHeader title={baseAsset} description="Asset intelligence: technicals, derivatives, sentiment, and AI analysis" />
      <AssetTopBar baseAsset={baseAsset} />

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="h-auto flex-wrap">
          {TAB_ITEMS.map((item) => (
            <TabsTrigger key={item.value} value={item.value}>
              {item.label}
            </TabsTrigger>
          ))}
        </TabsList>

        <TabsContent value="overview">
          <OverviewTab symbol={tradingPair} baseAsset={baseAsset} />
        </TabsContent>
        <TabsContent value="technical">
          <TechnicalTab baseAsset={baseAsset} />
        </TabsContent>
        <TabsContent value="derivatives">
          <DerivativesTab baseAsset={baseAsset} />
        </TabsContent>
        <TabsContent value="whales">
          <WhalesTab baseAsset={baseAsset} />
        </TabsContent>
        <TabsContent value="news">
          <NewsTab baseAsset={baseAsset} />
        </TabsContent>
        <TabsContent value="macro">
          <MacroTab baseAsset={baseAsset} />
        </TabsContent>
        <TabsContent value="sentiment">
          <SentimentTab baseAsset={baseAsset} />
        </TabsContent>
        <TabsContent value="ai-analysis">
          <AiAnalysisTab baseAsset={baseAsset} />
        </TabsContent>
        <TabsContent value="history">
          <HistoryTab baseAsset={baseAsset} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
