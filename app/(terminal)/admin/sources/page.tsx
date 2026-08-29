"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";

import { fetchAdminSources, updateAdminSource } from "@/services/admin-service";
import { PageHeader } from "@/components/common/page-header";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function AdminSourcesPage() {
  const queryClient = useQueryClient();

  const { data: sources, isLoading } = useQuery({
    queryKey: ["admin-sources"],
    queryFn: fetchAdminSources,
    refetchInterval: 30_000,
  });

  async function handleToggle(sourceId: string, field: "enabled" | "autoPublish", value: boolean) {
    await updateAdminSource(sourceId, { [field]: value });
    await queryClient.invalidateQueries({ queryKey: ["admin-sources"] });
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="News Sources"
        description="RSS sources the ingestion pipeline polls. Disabling a source or turning off auto-publish takes effect on the next poll cycle — no deploy needed."
      />

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 6 }).map((_, index) => (
            <Skeleton key={index} className="h-12 rounded-lg" />
          ))}
        </div>
      ) : !sources || sources.length === 0 ? (
        <p className="text-sm text-muted-foreground">No sources configured yet.</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Source</TableHead>
              <TableHead>Language</TableHead>
              <TableHead>Topic</TableHead>
              <TableHead>Trust</TableHead>
              <TableHead>Imported</TableHead>
              <TableHead>Last Status</TableHead>
              <TableHead>Enabled</TableHead>
              <TableHead>Auto-Publish</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {sources.map((source) => (
              <TableRow key={source.id}>
                <TableCell>
                  <div className="font-medium text-foreground">{source.name}</div>
                  <div className="text-xs text-muted-foreground">{source.rssUrl}</div>
                </TableCell>
                <TableCell className="uppercase text-muted-foreground">{source.language}</TableCell>
                <TableCell>
                  <Badge variant="outline">{source.defaultTopic}</Badge>
                </TableCell>
                <TableCell>{source.trustScore.toFixed(0)}</TableCell>
                <TableCell>{source.articlesImportedCount.toLocaleString()}</TableCell>
                <TableCell>
                  {source.lastStatus ? (
                    <Badge variant={source.lastStatus === "SUCCESS" ? "accent" : "danger"}>{source.lastStatus}</Badge>
                  ) : (
                    <span className="text-xs text-muted-foreground">Never polled</span>
                  )}
                </TableCell>
                <TableCell>
                  <Switch
                    checked={source.enabled}
                    onCheckedChange={(checked) => handleToggle(source.id, "enabled", checked)}
                  />
                </TableCell>
                <TableCell>
                  <Switch
                    checked={source.autoPublish}
                    onCheckedChange={(checked) => handleToggle(source.id, "autoPublish", checked)}
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
