"use client";

import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchBookmarks, removeBookmark } from "@/services/user-dashboard-service";
import { PageHeader } from "@/components/common/page-header";
import { PortalNewsCard } from "@/components/portal/news-card";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

export default function SavedNewsPage() {
  const queryClient = useQueryClient();
  const { data: articles, isLoading } = useQuery({ queryKey: ["bookmarks"], queryFn: fetchBookmarks });

  async function handleRemove(articleId: string) {
    await removeBookmark(articleId);
    await queryClient.invalidateQueries({ queryKey: ["bookmarks"] });
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Saved News" description="Articles you've bookmarked from the news portal" />

      {isLoading ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 3 }).map((_, index) => (
            <Skeleton key={index} className="h-[190px] rounded-xl" />
          ))}
        </div>
      ) : !articles || articles.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Nothing saved yet — bookmark an article from the{" "}
          <Link href="/" className="text-accent hover:underline">
            news portal
          </Link>
          .
        </p>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {articles.map((article) => (
            <div key={article.id} className="space-y-2">
              <PortalNewsCard news={article} />
              <Button variant="ghost" size="sm" onClick={() => handleRemove(article.id)}>
                Remove
              </Button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
