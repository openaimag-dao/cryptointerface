import type { Metadata } from "next";
import { cookies } from "next/headers";

import { parsePageParam } from "@/lib/pagination";
import { PORTAL_LANGUAGE_COOKIE, portalStrings, resolvePortalLanguage } from "@/lib/portal-i18n";
import { PageHeader } from "@/components/common/page-header";
import { PortalNewsCard } from "@/components/portal/news-card";
import { PortalPagination } from "@/components/portal/pagination";
import { Button } from "@/components/ui/button";
import { searchNews } from "@/services/news-service";

const PAGE_SIZE = 24;

interface SearchPageProps {
  searchParams: Promise<{ q?: string; page?: string }>;
}

// Query-driven results have no stable canonical content, so keep it out of
// the index while still letting people who land here directly use it.
export const metadata: Metadata = {
  title: "Search",
  robots: { index: false, follow: true },
};

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const { q, page: pageParam } = await searchParams;
  const query = q?.trim() ?? "";
  const page = parsePageParam(pageParam);
  const lang = resolvePortalLanguage((await cookies()).get(PORTAL_LANGUAGE_COOKIE)?.value);
  const t = portalStrings(lang);
  const result = query ? await searchNews(query, undefined, PAGE_SIZE, (page - 1) * PAGE_SIZE, lang) : null;
  const items = result?.items ?? [];
  const totalPages = result ? Math.max(1, Math.ceil(result.total / PAGE_SIZE)) : 1;

  return (
    <div className="space-y-8">
      <PageHeader
        title={t.searchTitle}
        description={result ? t.searchMatched(result.total) : t.searchDefaultDescription}
        serif
      />

      <form action="/search" method="get" className="flex gap-2">
        <input
          type="text"
          name="q"
          defaultValue={query}
          placeholder={t.searchPlaceholder}
          className="w-full rounded-md border border-border-strong bg-transparent px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent"
        />
        <Button type="submit">{t.searchButton}</Button>
      </form>

      {query && items.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t.searchNoResults(query)}</p>
      ) : null}

      {items.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {items.map((item) => (
            <PortalNewsCard key={item.id} news={item} />
          ))}
        </div>
      ) : null}

      {query ? (
        <PortalPagination basePath="/search" page={page} totalPages={totalPages} extraParams={{ q: query }} />
      ) : null}
    </div>
  );
}
