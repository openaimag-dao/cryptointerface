import type { Metadata } from "next";
import { cookies } from "next/headers";
import { notFound } from "next/navigation";

import { PageHeader } from "@/components/common/page-header";
import { DigestCard } from "@/components/portal/digest-card";
import { FearGreedWidget } from "@/components/portal/fear-greed-widget";
import { HeadlineListWidget } from "@/components/portal/headline-list-widget";
import { MarketMoversWidget } from "@/components/portal/market-movers-widget";
import { MarketSnapshotWidget } from "@/components/portal/market-snapshot-widget";
import { MiniHeatmapWidget } from "@/components/portal/mini-heatmap-widget";
import { PortalNewsCard } from "@/components/portal/news-card";
import { PortalPagination } from "@/components/portal/pagination";
import { parsePageParam } from "@/lib/pagination";
import { PORTAL_TOPICS, portalTopicForSlug } from "@/lib/portal-topics";
import { PORTAL_LANGUAGE_COOKIE, portalStrings, resolvePortalLanguage, topicStrings } from "@/lib/portal-i18n";
import { fetchNewsDigest, fetchPortalNews } from "@/services/news-service";
import { fetchPortalMacroIndicators } from "@/services/portal-macro-service";
import { fetchPortalPrices } from "@/services/portal-market-service";

const PAGE_SIZE = 24;
const OTHER_SECTIONS_WIDGET_SIZE = 4;

interface CategoryPageProps {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ page?: string }>;
}

export async function generateMetadata({ params }: CategoryPageProps): Promise<Metadata> {
  const { slug } = await params;
  const topic = portalTopicForSlug(slug);
  if (!topic) return {};

  return {
    title: topic.label,
    description: topic.description,
    alternates: { canonical: `/category/${topic.slug}` },
    openGraph: { title: topic.label, description: topic.description },
  };
}

export default async function CategoryPage({ params, searchParams }: CategoryPageProps) {
  const { slug } = await params;
  const topic = portalTopicForSlug(slug);
  if (!topic) notFound();

  const { page: pageParam } = await searchParams;
  const page = parsePageParam(pageParam);
  const lang = resolvePortalLanguage((await cookies()).get(PORTAL_LANGUAGE_COOKIE)?.value);
  const t = portalStrings(lang);
  const localizedTopic = topicStrings(lang, topic.value);
  // The other sections, for a "keep reading elsewhere" rail — real portal
  // category pages always cross-link into sibling sections rather than
  // dead-ending once you've read everything here.
  const otherTopics = PORTAL_TOPICS.filter((otherTopic) => otherTopic.slug !== topic.slug);
  const [result, digest, otherSectionPages, marketAssets, macroIndicators] = await Promise.all([
    fetchPortalNews(topic.value, PAGE_SIZE, (page - 1) * PAGE_SIZE, lang),
    page === 1 ? fetchNewsDigest(topic.value) : Promise.resolve(null),
    page === 1
      ? Promise.all(otherTopics.map((t) => fetchPortalNews(t.value, OTHER_SECTIONS_WIDGET_SIZE, 0, lang)))
      : Promise.resolve([]),
    fetchPortalPrices(),
    fetchPortalMacroIndicators(),
  ]);
  const otherSectionWidgets = otherSectionPages.map((p) => p?.items ?? []);
  const items = result?.items ?? [];
  const totalPages = result ? Math.max(1, Math.ceil(result.total / PAGE_SIZE)) : 1;

  return (
    <div className="space-y-8">
      <PageHeader title={localizedTopic.label} description={localizedTopic.description} serif />

      {digest ? <DigestCard digest={digest} lang={lang} /> : null}

      <div className="grid grid-cols-1 items-start gap-8 lg:grid-cols-[minmax(0,1fr)_300px]">
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t.categoryNoArticles(localizedTopic.label)}</p>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {items.map((item) => (
              <PortalNewsCard key={item.id} news={item} lang={lang} />
            ))}
          </div>
        )}

        {otherSectionWidgets.some((widgetItems) => widgetItems.length > 0) ||
        marketAssets.length > 0 ||
        macroIndicators.length > 0 ? (
          <aside className="space-y-6">
            {otherTopics.map((otherTopic, index) => (
              <HeadlineListWidget
                key={otherTopic.slug}
                title={topicStrings(lang, otherTopic.value).label}
                items={otherSectionWidgets[index] ?? []}
                lang={lang}
                seeAllHref={`/category/${otherTopic.slug}`}
                seeAllLabel={t.homeSeeAll}
              />
            ))}
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

      <PortalPagination basePath={`/category/${topic.slug}`} page={page} totalPages={totalPages} />
    </div>
  );
}
