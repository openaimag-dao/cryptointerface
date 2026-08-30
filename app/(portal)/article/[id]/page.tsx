import type { Metadata } from "next";
import Link from "next/link";
import { cookies } from "next/headers";
import { notFound } from "next/navigation";
import { ExternalLink, Sparkles } from "lucide-react";

import { timeAgo } from "@/lib/utils";
import { PORTAL_LANGUAGE_COOKIE, portalStrings, resolvePortalLanguage, topicStrings } from "@/lib/portal-i18n";
import { portalTopicForValue } from "@/lib/portal-topics";
import { fetchArticleById, fetchPortalNews } from "@/services/news-service";
import { ArticleImage } from "@/components/portal/article-image";
import { HeadlineListWidget } from "@/components/portal/headline-list-widget";
import { Badge } from "@/components/ui/badge";
import { SentimentBadge } from "@/components/common/sentiment-badge";
import { SaveArticleButton } from "@/components/portal/save-article-button";

const MORE_FROM_TOPIC_SIZE = 5;

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
      images: article.imageUrl ? [{ url: article.imageUrl }] : undefined,
    },
    twitter: {
      card: article.imageUrl ? "summary_large_image" : "summary",
      title: article.title,
      description: article.summary,
    },
  };
}

export default async function ArticlePage({ params }: ArticlePageProps) {
  const { id } = await params;
  const lang = resolvePortalLanguage((await cookies()).get(PORTAL_LANGUAGE_COOKIE)?.value);
  const t = portalStrings(lang);
  const article = await fetchArticleById(id, lang);
  if (!article) notFound();

  // "More from [topic]" rail — fetch one extra so excluding this article
  // (topic feeds aren't guaranteed to omit it) still leaves a full widget.
  const moreFromTopic = article.portalTopic
    ? (await fetchPortalNews(article.portalTopic, MORE_FROM_TOPIC_SIZE + 1, 0, lang))?.items
        .filter((item) => item.id !== article.id)
        .slice(0, MORE_FROM_TOPIC_SIZE) ?? []
    : [];
  const topicDef = article.portalTopic ? portalTopicForValue(article.portalTopic) : undefined;

  return (
    <div className="mx-auto grid max-w-6xl grid-cols-1 items-start gap-10 lg:grid-cols-[minmax(0,1fr)_300px]">
      <article className="space-y-6">
        <div>
          <Link href="/" className="text-xs text-muted-foreground transition-colors hover:text-accent">
            {t.articleBack}
          </Link>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs font-medium uppercase tracking-wider text-muted-foreground">
          <span>{article.source}</span>
          <span>·</span>
          <span>{article.category}</span>
          <span>·</span>
          <span>{timeAgo(article.publishedAt, lang)}</span>
        </div>

        <h1 className="font-serif text-3xl font-semibold leading-tight tracking-tight text-foreground sm:text-4xl">
          {article.title}
        </h1>

        <div className="flex flex-wrap items-center gap-2">
          <SentimentBadge sentiment={article.sentiment} />
          {article.portalTopic ? <Badge variant="outline">{article.portalTopic}</Badge> : null}
          {article.symbols.map((symbol) => (
            <Badge key={symbol} variant="outline">
              {symbol}
            </Badge>
          ))}
          <span className="ml-auto">
            <SaveArticleButton articleId={article.id} />
          </span>
        </div>

        {article.imageUrl ? (
          <ArticleImage src={article.imageUrl} className="aspect-[16/9] w-full rounded-lg object-cover" />
        ) : null}

        {/* AI Summary (Q4) is only ever generated in English, so it's shown
            only in the English reading mode — a mismatched-language box
            would read as broken rather than helpful. */}
        {article.aiSummary && lang === "en" ? (
          <div className="rounded-lg border border-accent/25 bg-accent-dim/40 p-4">
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-accent">
              <Sparkles className="size-3.5" />
              {t.articleAiSummary}
            </span>
            <p className="mt-2 text-sm leading-relaxed text-foreground">{article.aiSummary}</p>
            <p className="mt-2 text-[11px] text-muted-foreground">{t.articleAiSummaryDisclaimer}</p>
          </div>
        ) : null}

        <p className="text-base leading-relaxed text-foreground">{article.summary}</p>

        <a
          href={article.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-1.5 rounded-md border border-border-strong px-4 py-2 text-sm font-semibold text-foreground transition-colors hover:border-accent hover:text-accent"
        >
          {t.articleReadFullAt(article.source)}
          <ExternalLink className="size-3.5" />
        </a>
      </article>

      {moreFromTopic.length > 0 && topicDef ? (
        <aside className="lg:sticky lg:top-6 lg:self-start">
          <HeadlineListWidget
            title={topicStrings(lang, topicDef.value).label}
            items={moreFromTopic}
            lang={lang}
            seeAllHref={`/category/${topicDef.slug}`}
            seeAllLabel={t.homeSeeAll}
            leadImage
          />
        </aside>
      ) : null}
    </div>
  );
}
