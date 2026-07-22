"use client";

import { WATCHLIST_SYMBOLS } from "@/lib/constants";
import { useAssets } from "@/hooks/use-market-data";
import { orderedWatchlistSymbols, useWatchlistStore } from "@/store/watchlist-store";
import { AssetCard } from "@/components/dashboard/asset-card";
import { Skeleton } from "@/components/ui/skeleton";

export function AssetCardGrid() {
  const { data: assets, isLoading } = useAssets();
  const items = useWatchlistStore((state) => state.items);

  if (isLoading || !assets) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {WATCHLIST_SYMBOLS.map((symbol) => (
          <Skeleton key={symbol} className="h-[152px] rounded-xl" />
        ))}
      </div>
    );
  }

  const userSymbols = orderedWatchlistSymbols(items);
  const symbols = userSymbols.length > 0 ? userSymbols : WATCHLIST_SYMBOLS;
  const watchlist = symbols.map((symbol) => assets.find((asset) => asset.symbol === symbol)).filter(
    (asset): asset is NonNullable<typeof asset> => Boolean(asset),
  );

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {watchlist.map((asset, index) => (
        <AssetCard key={asset.symbol} asset={asset} index={index} showWatchlistControls={userSymbols.length > 0} />
      ))}
    </div>
  );
}
