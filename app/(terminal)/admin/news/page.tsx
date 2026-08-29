"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ExternalLink } from "lucide-react";

import { fetchAdminNews, fetchAdminNewsCounts, updateAdminNews } from "@/services/admin-service";
import { EDITORIAL_STATUSES, type EditorialStatus } from "@/types";
import { PageHeader } from "@/components/common/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";

const PAGE_SIZE = 20;

const STATUS_LABELS: Record<EditorialStatus, string> = {
  IMPORTED: "Imported",
  PROCESSING: "Processing",
  PENDING_REVIEW: "Pending Review",
  APPROVED: "Approved",
  PUBLISHED: "Published",
  REJECTED: "Rejected",
  ARCHIVED: "Archived",
};

interface StatusAction {
  label: string;
  targetStatus: EditorialStatus;
  variant: "default" | "danger" | "outline";
}

function actionsForStatus(status: EditorialStatus): StatusAction[] {
  switch (status) {
    case "PENDING_REVIEW":
      return [
        { label: "Approve & Publish", targetStatus: "PUBLISHED", variant: "default" },
        { label: "Reject", targetStatus: "REJECTED", variant: "danger" },
      ];
    case "APPROVED":
      return [
        { label: "Publish", targetStatus: "PUBLISHED", variant: "default" },
        { label: "Reject", targetStatus: "REJECTED", variant: "danger" },
      ];
    case "PUBLISHED":
      return [{ label: "Archive", targetStatus: "ARCHIVED", variant: "outline" }];
    case "REJECTED":
      return [{ label: "Restore to queue", targetStatus: "PENDING_REVIEW", variant: "outline" }];
    default:
      return [];
  }
}

export default function AdminNewsPage() {
  const [status, setStatus] = useState<EditorialStatus>("PENDING_REVIEW");
  const [offset, setOffset] = useState(0);
  const queryClient = useQueryClient();

  const { data: counts } = useQuery({
    queryKey: ["admin-news-counts"],
    queryFn: fetchAdminNewsCounts,
    refetchInterval: 30_000,
  });

  const { data: page, isLoading } = useQuery({
    queryKey: ["admin-news", status, offset],
    queryFn: () => fetchAdminNews(status, PAGE_SIZE, offset),
  });

  function handleStatusChange(next: string) {
    setStatus(next as EditorialStatus);
    setOffset(0);
  }

  async function handleTransition(articleId: string, targetStatus: EditorialStatus) {
    const updated = await updateAdminNews(articleId, { editorialStatus: targetStatus });
    if (!updated) return;
    await Promise.all([
      queryClient.invalidateQueries({ queryKey: ["admin-news"] }),
      queryClient.invalidateQueries({ queryKey: ["admin-news-counts"] }),
    ]);
  }

  const total = page?.total ?? 0;
  const hasNext = offset + PAGE_SIZE < total;
  const hasPrev = offset > 0;

  return (
    <div className="space-y-6">
      <PageHeader
        title="News Moderation"
        description="Review imported articles through the editorial workflow before they publish to the portal."
      />

      <Tabs value={status} onValueChange={handleStatusChange}>
        <TabsList className="h-auto flex-wrap gap-1">
          {EDITORIAL_STATUSES.map((s) => (
            <TabsTrigger key={s} value={s} className="gap-1.5">
              {STATUS_LABELS[s]}
              <Badge variant={s === status ? "accent" : "default"} className="px-1.5 py-0 text-[10px]">
                {counts?.[s] ?? 0}
              </Badge>
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, index) => (
            <Skeleton key={index} className="h-[104px] rounded-xl" />
          ))}
        </div>
      ) : !page || page.items.length === 0 ? (
        <p className="text-sm text-muted-foreground">No articles in {STATUS_LABELS[status]}.</p>
      ) : (
        <div className="space-y-3">
          {page.items.map((article) => (
            <Card key={article.id}>
              <CardContent className="flex flex-wrap items-start justify-between gap-4 p-4">
                <div className="min-w-0 flex-1 space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
                    <span className="font-medium text-foreground">{article.source}</span>
                    <span>&middot;</span>
                    <span>{new Date(article.publishedAt).toLocaleString()}</span>
                    {article.portalTopic ? <Badge variant="outline">{article.portalTopic}</Badge> : null}
                    <Badge variant="outline">{article.category}</Badge>
                  </div>
                  <h3 className="text-sm font-semibold text-foreground">{article.title}</h3>
                  <p className="line-clamp-2 text-sm text-muted-foreground">{article.summary}</p>
                  <a
                    href={article.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-accent hover:underline"
                  >
                    Source article <ExternalLink className="size-3" />
                  </a>
                </div>
                <div className="flex shrink-0 flex-col gap-2">
                  {actionsForStatus(status).map((action) => (
                    <Button
                      key={action.targetStatus}
                      size="sm"
                      variant={action.variant}
                      onClick={() => handleTransition(article.id, action.targetStatus)}
                    >
                      {action.label}
                    </Button>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {total > PAGE_SIZE && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            {offset + 1}-{Math.min(offset + PAGE_SIZE, total)} of {total}
          </span>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              disabled={!hasPrev}
              onClick={() => setOffset((o) => Math.max(0, o - PAGE_SIZE))}
            >
              Previous
            </Button>
            <Button size="sm" variant="outline" disabled={!hasNext} onClick={() => setOffset((o) => o + PAGE_SIZE)}>
              Next
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
