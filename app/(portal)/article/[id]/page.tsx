import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ExternalLink } from "lucide-react";

import { timeAgo } from "@/lib/utils";
import { fetchArticleById } from "@/services/news-service";
import { Badge } from "@/components/ui/badge";
import { SentimentBadge } from "@/components/common/sentiment-badge";

interface ArticlePageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: ArticlePageProps): Promise<Metadata> {
  const { id } = await params;
  const article = await fetchArticleById(id);
  if (!article) return {};

  return {
    title: article.title,
    description: article.summary,
    alternates: { canonical: `/article/${article.id}` },
    openGraph: {
      type: "article",
      title: article.title,
      description: article.summary,
      publishedTime: article.publishedAt,
      tags: article.symbols,
    },
    twitter: {
      card: "summary",
      title: article.title,
      description: article.summary,
    },
  };
}

export default async function ArticlePage({ params }: ArticlePageProps) {
  const { id } = await params;
  const article = await fetchArticleById(id);
  if (!article) notFound();

  return (
    <article className="mx-auto max-w-3xl space-y-6">
      <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
        <span>{article.source}</span>
        <span>·</span>
        <span>{article.category}</span>
        <span>·</span>
        <span>{timeAgo(article.publishedAt)}</span>
      </div>

      <h1 className="text-2xl font-semibold leading-tight tracking-tight text-foreground">{article.title}</h1>

      <div className="flex flex-wrap items-center gap-2">
        <SentimentBadge sentiment={article.sentiment} />
        {article.portalTopic ? <Badge variant="outline">{article.portalTopic}</Badge> : null}
        {article.symbols.map((symbol) => (
          <Badge key={symbol} variant="outline">
            {symbol}
          </Badge>
        ))}
      </div>

      <p className="text-sm leading-relaxed text-muted-foreground">{article.summary}</p>

      <a
        href={article.url}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1.5 text-sm font-medium text-accent transition-colors hover:text-accent/80"
      >
        Read the full article at {article.source}
        <ExternalLink className="size-3.5" />
      </a>

      <div>
        <Link href="/" className="text-xs text-muted-foreground transition-colors hover:text-foreground">
          ← Back to AIMAG News
        </Link>
      </div>
    </article>
  );
}
