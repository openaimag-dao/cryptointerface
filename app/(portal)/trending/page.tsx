import type { Metadata } from "next";
import Link from "next/link";
import { cookies } from "next/headers";

import { PORTAL_TOPICS, portalTopicForSlug } from "@/lib/portal-topics";
import { PORTAL_LANGUAGE_COOKIE, portalStrings, resolvePortalLanguage, topicStrings } from "@/lib/portal-i18n";
import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/common/page-header";
import { PortalNewsCard } from "@/components/portal/news-card";
import { fetchTrendingNews } from "@/services/news-service";

interface TrendingPageProps {
  searchParams: Promise<{ topic?: string }>;
}

export const metadata: Metadata = {
  title: "Trending",
  description: "The most significant Crypto, AI, Blockchain, and Innovation stories right now",
  alternates: { canonical: "/trending" },
  openGraph: {
    title: "Trending",
    description: "The most significant Crypto, AI, Blockchain, and Innovation stories right now",
  },
};

export default async function TrendingPage({ searchParams }: TrendingPageProps) {
  const { topic: topicSlug } = await searchParams;
  const topic = topicSlug ? portalTopicForSlug(topicSlug) : undefined;
  const lang = resolvePortalLanguage((await cookies()).get(PORTAL_LANGUAGE_COOKIE)?.value);
  const t = portalStrings(lang);
  const items = await fetchTrendingNews(topic?.value, 20, lang);

  return (
    <div className="space-y-8">
      <PageHeader title={t.trendingTitle} description={t.trendingDescription} serif />

      <nav className="flex flex-wrap gap-2 text-sm">
        <Link
          href="/trending"
          className={cn(
            "rounded-full border px-3 py-1 transition-colors",
            !topic
              ? "border-accent/30 bg-accent-dim text-accent"
              : "border-border-subtle text-muted-foreground hover:text-foreground",
          )}
        >
          {t.trendingAll}
        </Link>
        {PORTAL_TOPICS.map((topicItem) => (
          <Link
            key={topicItem.slug}
            href={`/trending?topic=${topicItem.slug}`}
            className={cn(
              "rounded-full border px-3 py-1 transition-colors",
              topic?.slug === topicItem.slug
                ? "border-accent/30 bg-accent-dim text-accent"
                : "border-border-subtle text-muted-foreground hover:text-foreground",
            )}
          >
            {topicStrings(lang, topicItem.value).label}
          </Link>
        ))}
      </nav>

      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground">{t.trendingEmpty}</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {items.map((item, index) => (
            <div key={item.id} className="relative">
              <span className="absolute -left-2 -top-2 z-10 flex size-6 items-center justify-center rounded-full bg-accent text-xs font-bold text-accent-foreground">
                {index + 1}
              </span>
              <PortalNewsCard news={item} lang={lang} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
