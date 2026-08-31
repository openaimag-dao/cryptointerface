import Link from "next/link";
import { cookies } from "next/headers";

import { HeadlineListWidget } from "@/components/portal/headline-list-widget";
import { MarketMoversWidget } from "@/components/portal/market-movers-widget";
import { MarketSnapshotWidget } from "@/components/portal/market-snapshot-widget";
import { PortalNewsCard } from "@/components/portal/news-card";
import { PortalPagination } from "@/components/portal/pagination";
import { parsePageParam } from "@/lib/pagination";
import { PORTAL_TOPICS } from "@/lib/portal-topics";
import { PORTAL_LANGUAGE_COOKIE, portalStrings, resolvePortalLanguage, topicStrings } from "@/lib/portal-i18n";
import { fetchPortalNews, fetchTrendingNews } from "@/services/news-service";
import { fetchPortalMacroIndicators } from "@/services/portal-macro-service";
import { fetchPortalPrices } from "@/services/portal-market-service";

const PAGE_SIZE = 24;
// Each left-rail topic module: enough to feel like a real "block" without
// dwarfing the main feed next to it.
const TOPIC_WIDGET_SIZE = 4;

interface PortalHomePageProps {
  searchParams: Promise<{ page?: string }>;
}

export default async function PortalHomePage({ searchParams }: PortalHomePageProps) {
  const { page: pageParam } = await searchParams;
  const page = parsePageParam(pageParam);
  const isFirstPage = page === 1;
  const lang = resolvePortalLanguage((await cookies()).get(PORTAL_LANGUAGE_COOKIE)?.value);
  const t = portalStrings(lang);

  const [result, trending, topicWidgetPages, marketAssets, macroIndicators] = await Promise.all([
    fetchPortalNews(undefined, PAGE_SIZE, (page - 1) * PAGE_SIZE, lang),
    isFirstPage ? fetchTrendingNews(undefined, 6, lang) : Promise.resolve([]),
    // Left rail: one "block in block" module per section, latest-first so
    // it never sits empty for a niche topic the way a trending list
    // (which needs real cross-source coverage) sometimes does.
    isFirstPage
      ? Promise.all(PORTAL_TOPICS.map((topic) => fetchPortalNews(topic.value, TOPIC_WIDGET_SIZE, 0, lang)))
      : Promise.resolve([]),
    fetchPortalPrices(),
    fetchPortalMacroIndicators(),
  ]);
  const topicWidgets = topicWidgetPages.map((topicPage) => topicPage?.items ?? []);
  const items = result?.items ?? [];
  const totalPages = result ? Math.max(1, Math.ceil(result.total / PAGE_SIZE)) : 1;

  // Lead with the most significant story (trending #1), not just the most
  // recent one — a real editorial front page, not a reverse-chron feed.
  // Everything else in `items` still appears in the grid below, hero or
  // not, so nothing is hidden by featuring it.
  const hero = isFirstPage ? (trending[0] ?? items[0]) : null;
  const gridItems = hero ? items.filter((item) => item.id !== hero.id) : items;
  const sidebarTrending = trending.filter((item) => item.id !== hero?.id).slice(0, 5);

  return (
    <div className="space-y-10">
      <div className="flex flex-wrap gap-2">
        {PORTAL_TOPICS.map((topic) => (
          <Link
            key={topic.slug}
            href={`/category/${topic.slug}`}
            className="rounded-full border border-border-strong px-3 py-1 text-xs font-medium text-muted-foreground transition-colors hover:border-accent hover:text-accent"
          >
            {topicStrings(lang, topic.value).label}
          </Link>
        ))}
      </div>

      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t.homeNoArticles}</p>
      ) : (
        <div className="grid grid-cols-1 items-start gap-8 lg:grid-cols-[minmax(0,1fr)_300px] xl:grid-cols-[260px_minmax(0,1fr)_300px]">
          <aside className="hidden space-y-6 xl:block">
            {PORTAL_TOPICS.map((topic, index) => (
              <HeadlineListWidget
                key={topic.slug}
                title={topicStrings(lang, topic.value).label}
                items={topicWidgets[index] ?? []}
                lang={lang}
                seeAllHref={`/category/${topic.slug}`}
                seeAllLabel={t.homeSeeAll}
              />
            ))}
          </aside>

          <div className="space-y-8">
            {hero ? <PortalNewsCard news={hero} featured lang={lang} /> : null}

            {gridItems.length > 0 ? (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {gridItems.map((item) => (
                  <PortalNewsCard key={item.id} news={item} lang={lang} />
                ))}
              </div>
            ) : null}
          </div>

          {sidebarTrending.length > 0 || marketAssets.length > 0 || macroIndicators.length > 0 ? (
            <aside className="space-y-6 lg:sticky lg:top-6 lg:self-start">
              {sidebarTrending.length > 0 ? (
                <HeadlineListWidget
                  title={t.homeTrendingNow}
                  items={sidebarTrending}
                  lang={lang}
                  seeAllHref="/trending"
                  seeAllLabel={t.homeSeeAll}
                  numbered
                  leadImage
                />
              ) : null}
              <MarketMoversWidget
                assets={marketAssets}
                title={t.marketMovers}
                gainersLabel={t.topGainers}
                losersLabel={t.topLosers}
              />
              <MarketSnapshotWidget indicators={macroIndicators} title={t.marketSnapshot} lang={lang} />
            </aside>
          ) : null}
        </div>
      )}

      <PortalPagination basePath="/" page={page} totalPages={totalPages} />
    </div>
  );
}
