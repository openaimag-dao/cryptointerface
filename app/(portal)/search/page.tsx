import type { Metadata } from "next";

import { parsePageParam } from "@/lib/pagination";
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
  const result = query ? await searchNews(query, undefined, PAGE_SIZE, (page - 1) * PAGE_SIZE) : null;
  const items = result?.items ?? [];
  const totalPages = result ? Math.max(1, Math.ceil(result.total / PAGE_SIZE)) : 1;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Search"
        description={
          result
            ? `${result.total} article${result.total === 1 ? "" : "s"} matched`
            : "Search across all AIMAG News articles"
        }
      />

      <form action="/search" method="get" className="flex gap-2">
        <input
          type="text"
          name="q"
          defaultValue={query}
          placeholder="Search articles…"
          className="w-full rounded-md border border-border-strong bg-transparent px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-accent"
        />
        <Button type="submit">Search</Button>
      </form>

      {query && items.length === 0 ? (
        <p className="text-sm text-muted-foreground">No articles matched &ldquo;{query}&rdquo;.</p>
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
