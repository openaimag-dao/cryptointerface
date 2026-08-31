import Link from "next/link";

import { timeAgo } from "@/lib/utils";
import type { PortalLanguage } from "@/lib/portal-i18n";
import type { NewsItem } from "@/types";
import { ArticleImage } from "@/components/portal/article-image";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SentimentBadge } from "@/components/common/sentiment-badge";

interface PortalNewsCardProps {
  news: NewsItem;
  // The homepage's lead story renders larger with a taller image and a
  // bigger serif headline — everything else (grid cards, trending,
  // search results) uses the compact layout.
  featured?: boolean;
  lang?: PortalLanguage;
}

export function PortalNewsCard({ news, featured, lang = "en" }: PortalNewsCardProps) {
  return (
    <Card className="h-full overflow-hidden transition-colors hover:border-border-strong">
      {news.imageUrl ? (
        <ArticleImage
          src={news.imageUrl}
          href={`/article/${news.id}`}
          className={featured ? "block aspect-[16/9]" : "block aspect-[16/10]"}
        />
      ) : null}
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
        <span className="text-xs font-medium text-muted-foreground">
          {news.source} · {news.category}
        </span>
        <SentimentBadge sentiment={news.sentiment} />
      </CardHeader>
      <CardContent className="pt-0">
        <Link href={`/article/${news.id}`} className="group/link block">
          <h3
            className={
              featured
                ? "font-serif text-2xl font-semibold leading-tight text-foreground transition-colors group-hover/link:text-accent"
                : "font-serif text-lg font-semibold leading-snug text-foreground transition-colors group-hover/link:text-accent"
            }
          >
            {news.title}
          </h3>
        </Link>
        <p
          className={
            featured
              ? "mt-3 line-clamp-3 text-sm leading-relaxed text-muted-foreground"
              : "mt-2 line-clamp-2 text-sm leading-relaxed text-muted-foreground"
          }
        >
          {news.summary}
        </p>

        <div className="mt-3 flex flex-wrap items-center gap-1.5">
          {news.portalTopic ? <Badge variant="outline">{news.portalTopic}</Badge> : null}
          {news.symbols.map((symbol) => (
            <Link key={symbol} href={`/search?q=${symbol}`}>
              <Badge variant="outline" className="transition-colors hover:border-accent hover:text-accent">
                {symbol}
              </Badge>
            </Link>
          ))}
        </div>

        <div className="mt-4 text-xs text-muted-foreground">{timeAgo(news.publishedAt, lang)}</div>
      </CardContent>
    </Card>
  );
}
