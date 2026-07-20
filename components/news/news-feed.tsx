"use client";

import { useMemo, useState } from "react";

import { useNews } from "@/hooks/use-news";
import type { Sentiment } from "@/types";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Skeleton } from "@/components/ui/skeleton";
import { NewsCard } from "@/components/news/news-card";

const FILTERS: { label: string; value: Sentiment | "ALL" }[] = [
  { label: "All", value: "ALL" },
  { label: "Bullish", value: "BULLISH" },
  { label: "Bearish", value: "BEARISH" },
  { label: "Neutral", value: "NEUTRAL" },
];

export function NewsFeed() {
  const { data: news, isLoading } = useNews();
  const [filter, setFilter] = useState<Sentiment | "ALL">("ALL");

  const filteredNews = useMemo(() => {
    if (!news) return [];
    if (filter === "ALL") return news;
    return news.filter((item) => item.sentiment === filter);
  }, [news, filter]);

  return (
    <div className="space-y-4">
      <Tabs value={filter} onValueChange={(value) => setFilter(value as Sentiment | "ALL")}>
        <TabsList>
          {FILTERS.map((item) => (
            <TabsTrigger key={item.value} value={item.value}>
              {item.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {isLoading || !news ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, index) => (
            <Skeleton key={index} className="h-[190px] rounded-xl" />
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filteredNews.map((item, index) => (
            <NewsCard key={item.id} news={item} index={index} />
          ))}
        </div>
      )}
    </div>
  );
}
