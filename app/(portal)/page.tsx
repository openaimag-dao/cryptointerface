import Link from "next/link";

import { PortalNewsCard } from "@/components/portal/news-card";
import { PortalPagination } from "@/components/portal/pagination";
import { parsePageParam } from "@/lib/pagination";
import { PORTAL_TOPICS } from "@/lib/portal-topics";
import { fetchPortalNews, fetchTrendingNews } from "@/services/news-service";

const PAGE_SIZE = 24;

interface PortalHomePageProps {
  searchParams: Promise<{ page?: string }>;
}

export default async function PortalHomePage({ searchParams }: PortalHomePageProps) {
  const { page: pageParam } = await searchParams;
  const page = parsePageParam(pageParam);
  const isFirstPage = page === 1;

  const [result, trending] = await Promise.all([
    fetchPortalNews(undefined, PAGE_SIZE, (page - 1) * PAGE_SIZE),
    isFirstPage ? fetchTrendingNews(undefined, 6) : Promise.resolve([]),
  ]);
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
            {topic.label}
          </Link>
        ))}
      </div>

      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground">No articles yet. Check back soon.</p>
      ) : (
        <div className="grid grid-cols-1 items-start gap-10 lg:grid-cols-3">
          <div className="space-y-8 lg:col-span-2">
            {hero ? <PortalNewsCard news={hero} featured /> : null}

            {gridItems.length > 0 ? (
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                {gridItems.map((item) => (
                  <PortalNewsCard key={item.id} news={item} />
                ))}
              </div>
            ) : null}
          </div>

          {sidebarTrending.length > 0 ? (
            <aside className="space-y-4">
              <div className="flex items-center justify-between border-b border-border-strong pb-2">
                <h2 className="font-serif text-lg font-semibold text-foreground">Trending Now</h2>
                <Link href="/trending" className="text-xs font-medium text-accent hover:underline">
                  See all
                </Link>
              </div>
              <ol className="space-y-4">
                {sidebarTrending.map((item, index) => (
                  <li key={item.id} className="flex gap-3">
                    <span className="font-serif text-2xl font-semibold text-border-strong">{index + 2}</span>
                    <Link href={`/article/${item.id}`} className="group/link min-w-0">
                      <h3 className="text-sm font-semibold leading-snug text-foreground transition-colors group-hover/link:text-accent">
                        {item.title}
                      </h3>
                      <p className="mt-1 text-xs text-muted-foreground">{item.source}</p>
                    </Link>
                  </li>
                ))}
              </ol>
            </aside>
          ) : null}
        </div>
      )}

      <PortalPagination basePath="/" page={page} totalPages={totalPages} />
    </div>
  );
}
