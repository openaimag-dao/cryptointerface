import { notFound } from "next/navigation";

import { PageHeader } from "@/components/common/page-header";
import { PortalNewsCard } from "@/components/portal/news-card";
import { PortalPagination } from "@/components/portal/pagination";
import { parsePageParam } from "@/lib/pagination";
import { portalTopicForSlug } from "@/lib/portal-topics";
import { fetchPortalNews } from "@/services/news-service";

const PAGE_SIZE = 24;

interface CategoryPageProps {
  params: Promise<{ slug: string }>;
  searchParams: Promise<{ page?: string }>;
}

export default async function CategoryPage({ params, searchParams }: CategoryPageProps) {
  const { slug } = await params;
  const topic = portalTopicForSlug(slug);
  if (!topic) notFound();

  const { page: pageParam } = await searchParams;
  const page = parsePageParam(pageParam);
  const result = await fetchPortalNews(topic.value, PAGE_SIZE, (page - 1) * PAGE_SIZE);
  const items = result?.items ?? [];
  const totalPages = result ? Math.max(1, Math.ceil(result.total / PAGE_SIZE)) : 1;

  return (
    <div className="space-y-8">
      <PageHeader title={topic.label} description={topic.description} />

      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground">No {topic.label} articles yet. Check back soon.</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {items.map((item) => (
            <PortalNewsCard key={item.id} news={item} />
          ))}
        </div>
      )}

      <PortalPagination basePath={`/category/${topic.slug}`} page={page} totalPages={totalPages} />
    </div>
  );
}
