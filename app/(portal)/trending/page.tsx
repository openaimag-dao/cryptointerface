import type { Metadata } from "next";
import Link from "next/link";

import { PORTAL_TOPICS, portalTopicForSlug } from "@/lib/portal-topics";
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
  const items = await fetchTrendingNews(topic?.value);

  return (
    <div className="space-y-8">
      <PageHeader
        title="Trending"
        description="Ranked by real coverage: how many independent sources reported it and how significant the classifier scored it — not a fabricated view counter."
        serif
      />

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
          All
        </Link>
        {PORTAL_TOPICS.map((t) => (
          <Link
            key={t.slug}
            href={`/trending?topic=${t.slug}`}
            className={cn(
              "rounded-full border px-3 py-1 transition-colors",
              topic?.slug === t.slug
                ? "border-accent/30 bg-accent-dim text-accent"
                : "border-border-subtle text-muted-foreground hover:text-foreground",
            )}
          >
            {t.label}
          </Link>
        ))}
      </nav>

      {items.length === 0 ? (
        <p className="text-sm text-muted-foreground">Nothing trending in the last 48 hours yet. Check back soon.</p>
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {items.map((item, index) => (
            <div key={item.id} className="relative">
              <span className="absolute -left-2 -top-2 z-10 flex size-6 items-center justify-center rounded-full bg-accent text-xs font-bold text-accent-foreground">
                {index + 1}
              </span>
              <PortalNewsCard news={item} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
