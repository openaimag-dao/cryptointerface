import type { Metadata } from "next";
import { cookies } from "next/headers";
import { notFound } from "next/navigation";

import { PageHeader } from "@/components/common/page-header";
import { FearGreedWidget } from "@/components/portal/fear-greed-widget";
import { MarketMoversWidget } from "@/components/portal/market-movers-widget";
import { MarketSnapshotWidget } from "@/components/portal/market-snapshot-widget";
import { MiniHeatmapWidget } from "@/components/portal/mini-heatmap-widget";
import { PortalNewsCard } from "@/components/portal/news-card";
import { PortalPagination } from "@/components/portal/pagination";
import { parsePageParam } from "@/lib/pagination";
import { PORTAL_LANGUAGE_COOKIE, portalStrings, resolvePortalLanguage } from "@/lib/portal-i18n";
import { fetchTagNews } from "@/services/news-service";
import { fetchPortalMacroIndicators } from "@/services/portal-macro-service";
import { fetchPortalPrices } from "@/services/portal-market-service";

const PAGE_SIZE = 24;

interface TagPageProps {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ page?: string }>;
}

export async function generateMetadata({ params }: TagPageProps): Promise<Metadata> {
  const { slug } = await params;
  const page = await fetchTagNews(slug, 1, 0);
  if (!page) return {};

  return {
    title: page.entity.name,
    alternates: { canonical: `/tag/${slug}` },
    openGraph: { title: page.entity.name },
  };
}

export default async function TagPage({ params, searchParams }: TagPageProps) {
  const { slug } = await params;
  const { page: pageParam } = await searchParams;
  const page = parsePageParam(pageParam);
  const lang = resolvePortalLanguage((await cookies()).get(PORTAL_LANGUAGE_COOKIE)?.value);
  const t = portalStrings(lang);

  const [result, marketAssets, macroIndicators] = await Promise.all([
    fetchTagNews(slug, PAGE_SIZE, (page - 1) * PAGE_SIZE, lang),
    fetchPortalPrices(),
    fetchPortalMacroIndicators(),
  ]);
  if (!result) notFound();

  const items = result.items;
  const totalPages = Math.max(1, Math.ceil(result.total / PAGE_SIZE));

  return (
    <div className="space-y-8">
      <PageHeader title={t.tagArticles(result.entity.name)} serif />

      <div className="grid grid-cols-1 items-start gap-8 lg:grid-cols-[minmax(0,1fr)_300px]">
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t.tagEmpty(result.entity.name)}</p>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {items.map((item) => (
              <PortalNewsCard key={item.id} news={item} lang={lang} />
            ))}
          </div>
        )}

        {marketAssets.length > 0 || macroIndicators.length > 0 ? (
          <aside className="space-y-6">
            <FearGreedWidget indicators={macroIndicators} lang={lang} />
            <MarketMoversWidget
              assets={marketAssets}
              title={t.marketMovers}
              gainersLabel={t.topGainers}
              losersLabel={t.topLosers}
            />
            <MiniHeatmapWidget assets={marketAssets} title={t.heatmapTitle} />
            <MarketSnapshotWidget indicators={macroIndicators} title={t.marketSnapshot} lang={lang} />
          </aside>
        ) : null}
      </div>

      <PortalPagination basePath={`/tag/${slug}`} page={page} totalPages={totalPages} />
    </div>
  );
}
