import { PageHeader } from "@/components/common/page-header";
import { PortalNewsCard } from "@/components/portal/news-card";
import { Button } from "@/components/ui/button";
import { searchNews } from "@/services/news-service";

interface SearchPageProps {
  searchParams: Promise<{ q?: string }>;
}

export default async function SearchPage({ searchParams }: SearchPageProps) {
  const { q } = await searchParams;
  const query = q?.trim() ?? "";
  const results = query ? await searchNews(query) : [];

  return (
    <div className="space-y-8">
      <PageHeader title="Search" description="Search across all AIMAG News articles" />

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

      {query && results.length === 0 ? (
        <p className="text-sm text-muted-foreground">No articles matched &ldquo;{query}&rdquo;.</p>
      ) : null}

      {results.length > 0 ? (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {results.map((item) => (
            <PortalNewsCard key={item.id} news={item} />
          ))}
        </div>
      ) : null}
    </div>
  );
}
