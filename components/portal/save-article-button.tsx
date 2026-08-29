"use client";

import Link from "next/link";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Bookmark, BookmarkCheck } from "lucide-react";

import { useCurrentUser } from "@/hooks/use-current-user";
import { addBookmark, fetchBookmarks, removeBookmark } from "@/services/user-dashboard-service";
import { Button } from "@/components/ui/button";

export function SaveArticleButton({ articleId }: { articleId: string }) {
  const queryClient = useQueryClient();
  const { data: user, isLoading: isLoadingUser } = useCurrentUser();
  const { data: bookmarks } = useQuery({
    queryKey: ["bookmarks"],
    queryFn: fetchBookmarks,
    enabled: !!user,
  });

  const isSaved = bookmarks?.some((article) => article.id === articleId) ?? false;

  async function toggleSaved() {
    if (isSaved) {
      await removeBookmark(articleId);
    } else {
      await addBookmark(articleId);
    }
    await queryClient.invalidateQueries({ queryKey: ["bookmarks"] });
  }

  if (isLoadingUser) return null;

  if (!user) {
    return (
      <Button variant="outline" size="sm" asChild>
        <Link href={`/login?next=/article/${articleId}`}>
          <Bookmark className="size-3.5" />
          Sign in to save
        </Link>
      </Button>
    );
  }

  return (
    <Button variant="outline" size="sm" onClick={toggleSaved}>
      {isSaved ? <BookmarkCheck className="size-3.5" /> : <Bookmark className="size-3.5" />}
      {isSaved ? "Saved" : "Save"}
    </Button>
  );
}
