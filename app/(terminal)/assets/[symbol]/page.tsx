"use client";

import { useMemo, useState } from "react";
import { useParams } from "next/navigation";
import dynamic from "next/dynamic";

import { PageHeader } from "@/components/common/page-header";
import { AssetTopBar } from "@/components/assets/asset-top-bar";
import { TabPlaceholder } from "@/components/assets/tab-placeholder";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";

const OverviewTab = dynamic(() => import("@/components/assets/overview-tab").then((m) => m.OverviewTab), {
  loading: () => <Skeleton className="h-[420px] w-full rounded-lg" />,
});
const TechnicalTab = dynamic(() => import("@/components/assets/technical-tab").then((m) => m.TechnicalTab), {
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
        <TabsList className="flex-wrap">
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
          <TabPlaceholder label="Derivatives" />
        </TabsContent>
        <TabsContent value="whales">
          <TabPlaceholder label="Whale Intelligence" />
        </TabsContent>
        <TabsContent value="news">
          <TabPlaceholder label="News Center" />
        </TabsContent>
        <TabsContent value="macro">
          <TabPlaceholder label="Macro" />
        </TabsContent>
        <TabsContent value="sentiment">
          <TabPlaceholder label="Sentiment" />
        </TabsContent>
        <TabsContent value="ai-analysis">
          <TabPlaceholder label="AI Analysis" />
        </TabsContent>
        <TabsContent value="history">
          <TabPlaceholder label="Historical Behavior" />
        </TabsContent>
      </Tabs>
    </div>
  );
}
