import { PriceTickerLive } from "@/components/portal/price-ticker-live";
import { fetchPortalPrices } from "@/services/portal-market-service";

/**
 * Server-fetches the first snapshot (fast first paint, no client-side
 * loading flash) and hands off to a client component for live polling —
 * see PriceTickerLive / useLiveMarketPrices.
 */
export async function PriceTicker() {
  const assets = await fetchPortalPrices();
  if (assets.length === 0) return null;

  return <PriceTickerLive initialAssets={assets} />;
}
