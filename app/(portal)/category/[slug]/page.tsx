import type { Metadata } from "next";
import { cookies } from "next/headers";
import { notFound } from "next/navigation";

import { PageHeader } from "@/components/common/page-header";
import { DigestCard } from "@/components/portal/digest-card";
import { PortalNewsCard } from "@/components/portal/news-card";
import { PortalPagination } from "@/components/portal/pagination";
import { parsePageParam } from "@/lib/pagination";
import { portalTopicForSlug } from "@/lib/portal-topics";
import { PORTAL_LANGUAGE_COOKIE, portalStrings, resolvePortalLanguage, topicStrings } from "@/lib/portal-i18n";
import { fetchNewsDigest, fetchPortalNews } from "@/services/news-service";

const PAGE_SIZE = 24;

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
  const [result, digest] = await Promise.all([
    fetchPortalNews(topic.value, PAGE_SIZE, (page - 1) * PAGE_SIZE, lang),
    page === 1 ? fetchNewsDigest(topic.value) : Promise.resolve(null),
  ]);
  const items = result?.items ?? [];
  const totalPages = result ? Math.max(1, Math.ceil(result.total / PAGE_SIZE)) : 1;

  return (
    <div className="space-y-8">
      <PageHeader title={localizedTopic.label} description={localizedTopic.description} serif />

      {digest ? <DigestCard digest={digest} /> : null}

      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t.categoryNoArticles(localizedTopic.label)}</p>
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
