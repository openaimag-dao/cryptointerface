"use client";

import { useQuery } from "@tanstack/react-query";

import { timeAgo } from "@/lib/utils";
import { fetchAdminFetchLogs } from "@/services/admin-service";
import { PageHeader } from "@/components/common/page-header";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";

export default function AdminMonitoringPage() {
  const { data: logs, isLoading } = useQuery({
    queryKey: ["admin-fetch-logs"],
    queryFn: () => fetchAdminFetchLogs(100),
    refetchInterval: 30_000,
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Ingestion Monitoring"
        description="Real RSS poll history — every attempt logged, so a persistently-failing source is visible here rather than silently going quiet."
      />

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 8 }).map((_, index) => (
            <Skeleton key={index} className="h-10 rounded-lg" />
          ))}
        </div>
      ) : !logs || logs.length === 0 ? (
        <p className="text-sm text-muted-foreground">No fetch attempts logged yet.</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Source</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Found</TableHead>
              <TableHead>New</TableHead>
              <TableHead>Duration</TableHead>
              <TableHead>Error</TableHead>
              <TableHead>When</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {logs.map((log) => (
              <TableRow key={log.id}>
                <TableCell className="font-medium text-foreground">{log.sourceName}</TableCell>
                <TableCell>
                  <Badge variant={log.status === "SUCCESS" ? "accent" : "danger"}>{log.status}</Badge>
                </TableCell>
                <TableCell>{log.articlesFound}</TableCell>
                <TableCell>{log.articlesNew}</TableCell>
                <TableCell>{log.durationMs}ms</TableCell>
                <TableCell className={`max-w-xs truncate text-xs ${log.errorMessage ? "text-danger" : "text-muted-foreground"}`}>
                  {log.errorMessage ?? "—"}
                </TableCell>
                <TableCell className="text-xs text-muted-foreground">{timeAgo(log.createdAt)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </div>
  );
}
