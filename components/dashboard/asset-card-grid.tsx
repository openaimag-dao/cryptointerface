"use client";

import { WATCHLIST_SYMBOLS } from "@/lib/mock/assets";
import { useAssets } from "@/hooks/use-market-data";
import { AssetCard } from "@/components/dashboard/asset-card";
import { Skeleton } from "@/components/ui/skeleton";

export function AssetCardGrid() {
  const { data: assets, isLoading } = useAssets();

  if (isLoading || !assets) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {WATCHLIST_SYMBOLS.map((symbol) => (
          <Skeleton key={symbol} className="h-[152px] rounded-xl" />
        ))}
      </div>
    );
  }

  const watchlist = WATCHLIST_SYMBOLS.map((symbol) => assets.find((asset) => asset.symbol === symbol)).filter(
    (asset): asset is NonNullable<typeof asset> => Boolean(asset),
  );

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {watchlist.map((asset, index) => (
        <AssetCard key={asset.symbol} asset={asset} index={index} />
      ))}
    </div>
  );
}
