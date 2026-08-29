"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { X } from "lucide-react";

import { addToWatchlist, fetchWatchlist, removeFromWatchlist } from "@/services/user-dashboard-service";
import { PageHeader } from "@/components/common/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";

export default function WatchlistPage() {
  const queryClient = useQueryClient();
  const { data: symbols, isLoading } = useQuery({ queryKey: ["watchlist"], queryFn: fetchWatchlist });
  const [newSymbol, setNewSymbol] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function handleAdd(event: React.FormEvent) {
    event.preventDefault();
    if (!newSymbol.trim()) return;
    setError(null);
    const result = await addToWatchlist(newSymbol.trim());
    if (result === null) {
      setError("Couldn't add that symbol — the watchlist may be full.");
      return;
    }
    setNewSymbol("");
    queryClient.setQueryData(["watchlist"], result);
  }

  async function handleRemove(symbol: string) {
    const result = await removeFromWatchlist(symbol);
    if (result !== null) queryClient.setQueryData(["watchlist"], result);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Watchlist"
        description="Symbols you're tracking — live market data lands in a future update"
      />

      <form onSubmit={handleAdd} className="flex max-w-sm gap-2">
        <Input
          placeholder="e.g. BTC"
          value={newSymbol}
          onChange={(e) => setNewSymbol(e.target.value)}
          maxLength={16}
        />
        <Button type="submit">Add</Button>
      </form>
      {error ? <p className="text-sm text-danger">{error}</p> : null}

      {isLoading ? (
        <Skeleton className="h-10 w-full max-w-sm rounded-lg" />
      ) : !symbols || symbols.length === 0 ? (
        <p className="text-sm text-muted-foreground">No symbols yet — add one above.</p>
      ) : (
        <div className="flex flex-wrap gap-2">
          {symbols.map((symbol) => (
            <Badge key={symbol} variant="outline" className="gap-1.5 py-1 pl-3 pr-1.5 text-sm">
              {symbol}
              <button
                type="button"
                onClick={() => handleRemove(symbol)}
                className="rounded-sm p-0.5 text-muted-foreground transition-colors hover:bg-white/[0.08] hover:text-foreground"
                aria-label={`Remove ${symbol} from watchlist`}
              >
                <X className="size-3" />
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}
