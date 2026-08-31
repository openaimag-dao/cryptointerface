import { SITE_URL } from "@/lib/env";
import { fetchPortalNews } from "@/services/news-service";

const FEED_SIZE = 50;

// RSS 2.0's own escaping rules (a strict subset of what XML needs for
// text nodes — '>' doesn't strictly need escaping there, but escaping it
// too is harmless and avoids relying on that nuance).
function escapeXml(value: string): string {
  return value
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

export async function GET() {
  const page = await fetchPortalNews(undefined, FEED_SIZE, 0);
  const articles = page?.items ?? [];

  const items = articles
    .map((article) => {
      const url = `${SITE_URL}/article/${article.id}`;
      return `    <item>
      <title>${escapeXml(article.title)}</title>
      <link>${url}</link>
      <guid isPermaLink="true">${url}</guid>
      <pubDate>${new Date(article.publishedAt).toUTCString()}</pubDate>
      <description>${escapeXml(article.summary)}</description>
      <source url="${escapeXml(article.url)}">${escapeXml(article.source)}</source>
      ${article.portalTopic ? `<category>${escapeXml(article.portalTopic)}</category>` : ""}
    </item>`;
    })
    .join("\n");

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>AIMAG News</title>
    <link>${SITE_URL}</link>
    <description>Crypto, AI, Blockchain &amp; Innovation headlines — aggregated from real sources and classified automatically.</description>
    <language>en</language>
    <atom:link href="${SITE_URL}/feed.xml" rel="self" type="application/rss+xml" />
${items}
  </channel>
</rss>`;

  return new Response(xml, {
    headers: {
      "Content-Type": "application/rss+xml; charset=utf-8",
      "Cache-Control": "public, max-age=0, s-maxage=900",
    },
  });
}
