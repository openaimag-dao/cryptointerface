import Link from "next/link";

import { timeAgo } from "@/lib/utils";
import type { NewsItem } from "@/types";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SentimentBadge } from "@/components/common/sentiment-badge";

export function PortalNewsCard({ news }: { news: NewsItem }) {
  return (
    <Card className="h-full transition-colors hover:border-border-strong">
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
        <span className="text-xs font-medium text-muted-foreground">
          {news.source} · {news.category}
        </span>
        <SentimentBadge sentiment={news.sentiment} />
      </CardHeader>
      <CardContent className="pt-0">
        <Link href={`/article/${news.id}`} className="group/link block">
          <h3 className="text-sm font-semibold leading-snug text-foreground transition-colors group-hover/link:text-accent">
            {news.title}
          </h3>
        </Link>
        <p className="mt-2 line-clamp-2 text-xs leading-relaxed text-muted-foreground">{news.summary}</p>

        <div className="mt-3 flex flex-wrap items-center gap-1.5">
          {news.portalTopic ? <Badge variant="outline">{news.portalTopic}</Badge> : null}
          {news.symbols.map((symbol) => (
            <Badge key={symbol} variant="outline">
              {symbol}
            </Badge>
          ))}
        </div>

        <div className="mt-4 text-xs text-muted-foreground">{timeAgo(news.publishedAt)}</div>
      </CardContent>
    </Card>
  );
}
