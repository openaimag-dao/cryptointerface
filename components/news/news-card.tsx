"use client";

import { motion } from "framer-motion";
import { ExternalLink } from "lucide-react";

import { timeAgo } from "@/lib/utils";
import type { NewsItem } from "@/types";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { SentimentBadge } from "@/components/common/sentiment-badge";

export function NewsCard({ news, index = 0 }: { news: NewsItem; index?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.03 }}
    >
      <Card className="group h-full transition-colors hover:border-border-strong">
        <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
          <span className="text-xs font-medium text-muted-foreground">
            {news.source} · {news.category}
          </span>
          <SentimentBadge sentiment={news.sentiment} />
        </CardHeader>
        <CardContent className="pt-0">
          <a href={news.url} target="_blank" rel="noopener noreferrer" className="group/link block">
            <h3 className="text-sm font-semibold leading-snug text-foreground transition-colors group-hover/link:text-accent">
              {news.title}
            </h3>
          </a>
          <p className="mt-2 line-clamp-2 text-xs leading-relaxed text-muted-foreground">{news.summary}</p>

          <div className="mt-3 flex flex-wrap items-center gap-1.5">
            {news.symbols.map((symbol) => (
              <Badge key={symbol} variant="outline">
                {symbol}
              </Badge>
            ))}
          </div>

          <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
            <span>{timeAgo(news.publishedAt)}</span>
            <ExternalLink className="size-3.5 opacity-0 transition-opacity group-hover:opacity-100" />
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
