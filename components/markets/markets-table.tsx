"use client";

import { useMemo, useState } from "react";
import { ArrowDown, ArrowUp, ArrowUpDown } from "lucide-react";

import { cn, formatCompactNumber, formatCurrency, formatPercent } from "@/lib/utils";
import { useAssets } from "@/hooks/use-market-data";
import type { AssetQuote } from "@/types";
import { Card } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Skeleton } from "@/components/ui/skeleton";
import { DirectionBadge } from "@/components/common/direction-badge";
import { AiScoreRing } from "@/components/common/ai-score-ring";

type SortKey = keyof Pick<
  AssetQuote,
  "symbol" | "price" | "changePercent24h" | "volume24h" | "fundingRate" | "openInterest" | "aiScore"
>;

interface Column {
  key: SortKey;
  label: string;
  align?: "left" | "right";
}

const COLUMNS: Column[] = [
  { key: "symbol", label: "Symbol", align: "left" },
  { key: "price", label: "Price", align: "right" },
  { key: "changePercent24h", label: "24h", align: "right" },
  { key: "volume24h", label: "Volume", align: "right" },
  { key: "fundingRate", label: "Funding", align: "right" },
  { key: "openInterest", label: "OI", align: "right" },
  { key: "aiScore", label: "AI Score", align: "right" },
];

export function MarketsTable() {
  const { data: assets, isLoading } = useAssets();
  const [sortKey, setSortKey] = useState<SortKey>("volume24h");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

  const sortedAssets = useMemo(() => {
    if (!assets) return [];
    const copy = [...assets];
    copy.sort((a, b) => {
      const aValue = a[sortKey];
      const bValue = b[sortKey];
      if (typeof aValue === "string" && typeof bValue === "string") {
        return sortDir === "asc" ? aValue.localeCompare(bValue) : bValue.localeCompare(aValue);
      }
      const aNum = Number(aValue);
      const bNum = Number(bValue);
      return sortDir === "asc" ? aNum - bNum : bNum - aNum;
    });
    return copy;
  }, [assets, sortKey, sortDir]);

  function toggleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDir((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("desc");
    }
  }

  return (
    <Card className="overflow-hidden">
      <div className="max-h-[calc(100vh-220px)] overflow-y-auto">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              {COLUMNS.map((column) => (
                <TableHead
                  key={column.key}
                  className={cn("cursor-pointer select-none", column.align === "right" && "text-right")}
                  onClick={() => toggleSort(column.key)}
                >
                  <span className={cn("inline-flex items-center gap-1", column.align === "right" && "flex-row-reverse")}>
                    {column.label}
                    {sortKey === column.key ? (
                      sortDir === "asc" ? (
                        <ArrowUp className="size-3" />
                      ) : (
                        <ArrowDown className="size-3" />
                      )
                    ) : (
                      <ArrowUpDown className="size-3 opacity-30" />
                    )}
                  </span>
                </TableHead>
              ))}
              <TableHead className="text-right">Direction</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading || !assets
              ? Array.from({ length: 8 }).map((_, index) => (
                  <TableRow key={index}>
                    {Array.from({ length: 8 }).map((__, cellIndex) => (
                      <TableCell key={cellIndex}>
                        <Skeleton className="h-4 w-full" />
                      </TableCell>
                    ))}
                  </TableRow>
                ))
              : sortedAssets.map((asset) => (
                  <TableRow key={asset.symbol}>
                    <TableCell className="font-medium text-foreground">
                      <div className="flex flex-col">
                        <span>{asset.symbol}</span>
                        <span className="text-xs font-normal text-muted-foreground">{asset.name}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-right">{formatCurrency(asset.price)}</TableCell>
                    <TableCell
                      className={cn(
                        "text-right",
                        asset.changePercent24h >= 0 ? "text-accent" : "text-danger",
                      )}
                    >
                      {formatPercent(asset.changePercent24h)}
                    </TableCell>
                    <TableCell className="text-right text-muted-foreground">
                      ${formatCompactNumber(asset.volume24h)}
                    </TableCell>
                    <TableCell
                      className={cn(
                        "text-right",
                        asset.fundingRate >= 0 ? "text-accent" : "text-danger",
                      )}
                    >
                      {formatPercent(asset.fundingRate * 100)}
                    </TableCell>
                    <TableCell className="text-right text-muted-foreground">
                      ${formatCompactNumber(asset.openInterest)}
                    </TableCell>
                    <TableCell>
                      <div className="flex justify-end">
                        <AiScoreRing score={asset.aiScore} size={34} strokeWidth={3} />
                      </div>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end">
                        <DirectionBadge direction={asset.direction} size="sm" />
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
          </TableBody>
        </Table>
      </div>
    </Card>
  );
}
