"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchBookmarks, removeBookmark } from "@/services/user-dashboard-service";
import type { PortalLanguage } from "@/lib/portal-i18n";
import { portalStrings } from "@/lib/portal-i18n";
import { PortalNewsCard } from "@/components/portal/news-card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

export function SavedArticlesGrid({ lang }: { lang: PortalLanguage }) {
  const t = portalStrings(lang);
  const queryClient = useQueryClient();
  const { data: articles, isLoading } = useQuery({ queryKey: ["bookmarks"], queryFn: fetchBookmarks });

  async function handleRemove(articleId: string) {
    await removeBookmark(articleId);
    await queryClient.invalidateQueries({ queryKey: ["bookmarks"] });
  }

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 3 }).map((_, index) => (
          <Skeleton key={index} className="h-[220px] rounded-xl" />
        ))}
      </div>
    );
  }

  if (!articles || articles.length === 0) {
    return <p className="text-sm text-muted-foreground">{t.savedEmpty}</p>;
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
      {articles.map((article) => (
        <div key={article.id} className="space-y-2">
          <PortalNewsCard news={article} lang={lang} />
          <Button variant="ghost" size="sm" onClick={() => handleRemove(article.id)}>
            {t.savedRemove}
          </Button>
        </div>
      ))}
    </div>
  );
}
