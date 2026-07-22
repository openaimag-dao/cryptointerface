"use client";

import { useAssetNews } from "@/hooks/use-asset";
import { Skeleton } from "@/components/ui/skeleton";
import { NewsCard } from "@/components/news/news-card";

interface NewsTabProps {
  baseAsset: string;
}

export function NewsTab({ baseAsset }: NewsTabProps) {
  const { data: news, isLoading } = useAssetNews(baseAsset);

  if (isLoading || !news) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <Skeleton key={i} className="h-[180px] rounded-xl" />
        ))}
      </div>
    );
  }

  if (news.length === 0) {
    return <p className="py-10 text-center text-sm text-muted-foreground">No recent news mentions {baseAsset}.</p>;
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
      {news.map((item, index) => (
        <NewsCard key={item.id} news={item} index={index} />
      ))}
    </div>
  );
}
