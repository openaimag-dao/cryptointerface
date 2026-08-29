import type { MetadataRoute } from "next";

import { SITE_URL } from "@/lib/env";
import { PORTAL_TOPICS } from "@/lib/portal-topics";
import { fetchPortalNews } from "@/services/news-service";
import type { NewsItem } from "@/types";

const MAX_ARTICLE_ENTRIES = 300;
const PAGE_SIZE = 100;

async function fetchRecentArticles(maxItems: number): Promise<NewsItem[]> {
  const items: NewsItem[] = [];
  let offset = 0;

  while (items.length < maxItems) {
    const page = await fetchPortalNews(undefined, PAGE_SIZE, offset);
    if (!page || page.items.length === 0) break;
    items.push(...page.items);
    if (page.items.length < PAGE_SIZE) break;
    offset += PAGE_SIZE;
  }

  return items.slice(0, maxItems);
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const staticEntries: MetadataRoute.Sitemap = [
    { url: SITE_URL, changeFrequency: "hourly", priority: 1 },
    { url: `${SITE_URL}/search`, changeFrequency: "monthly", priority: 0.3 },
    ...PORTAL_TOPICS.map((topic) => ({
      url: `${SITE_URL}/category/${topic.slug}`,
      changeFrequency: "hourly" as const,
      priority: 0.8,
    })),
  ];

  const articles = await fetchRecentArticles(MAX_ARTICLE_ENTRIES);
  const articleEntries: MetadataRoute.Sitemap = articles.map((article) => ({
    url: `${SITE_URL}/article/${article.id}`,
    lastModified: new Date(article.publishedAt),
    changeFrequency: "never",
    priority: 0.5,
  }));

  return [...staticEntries, ...articleEntries];
}
