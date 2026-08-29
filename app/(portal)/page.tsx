import Link from "next/link";

import { PageHeader } from "@/components/common/page-header";
import { PortalNewsCard } from "@/components/portal/news-card";
import { PortalPagination } from "@/components/portal/pagination";
import { parsePageParam } from "@/lib/pagination";
import { PORTAL_TOPICS } from "@/lib/portal-topics";
import { fetchPortalNews } from "@/services/news-service";

const PAGE_SIZE = 24;

interface PortalHomePageProps {
  searchParams: Promise<{ page?: string }>;
}

export default async function PortalHomePage({ searchParams }: PortalHomePageProps) {
  const { page: pageParam } = await searchParams;
  const page = parsePageParam(pageParam);
  const result = await fetchPortalNews(undefined, PAGE_SIZE, (page - 1) * PAGE_SIZE);
  const items = result?.items ?? [];
  const totalPages = result ? Math.max(1, Math.ceil(result.total / PAGE_SIZE)) : 1;

  return (
    <div className="space-y-8">
      <PageHeader
        title="AIMAG News"
        description="Crypto, AI, blockchain, and innovation headlines — aggregated and classified automatically."
      />

      <div className="flex flex-wrap gap-2">
        {PORTAL_TOPICS.map((topic) => (
          <Link
            key={topic.slug}
            href={`/category/${topic.slug}`}
            className="rounded-full border border-border-strong px-3 py-1 text-xs text-muted-foreground transition-colors hover:border-accent hover:text-foreground"
          >
            {topic.label}
          </Link>
        ))}
      </div>

      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground">No articles yet. Check back soon.</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {items.map((item) => (
            <PortalNewsCard key={item.id} news={item} />
          ))}
        </div>
      )}

      <PortalPagination basePath="/" page={page} totalPages={totalPages} />
    </div>
  );
}
