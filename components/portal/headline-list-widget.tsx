import Link from "next/link";

import { timeAgo } from "@/lib/utils";
import type { PortalLanguage } from "@/lib/portal-i18n";
import type { NewsItem } from "@/types";
import { ArticleImage } from "@/components/portal/article-image";

interface HeadlineListWidgetProps {
  title: string;
  items: NewsItem[];
  lang: PortalLanguage;
  seeAllHref?: string;
  seeAllLabel?: string;
  // Numbered rank (1, 2, 3…) for a "most significant" list like
  // trending; unnumbered for a plain "latest from this section" list —
  // numbering implies a ranking that only actually applies to one of them.
  numbered?: boolean;
  // Shows the lead item's image above the list — the "block in block"
  // treatment real portal sidebar modules use so every widget isn't just
  // a flat wall of text.
  leadImage?: boolean;
}

// One self-contained sidebar module — a bordered "block" with its own
// header and a compact headline list — the repeating unit both the
// per-topic rails and the trending rail are built from.
export function HeadlineListWidget({
  title,
  items,
  lang,
  seeAllHref,
  seeAllLabel,
  numbered = false,
  leadImage = false,
}: HeadlineListWidgetProps) {
  if (items.length === 0) return null;

  const [lead, ...rest] = items;

  return (
    <section className="glass-panel rounded-xl p-4">
      <div className="flex items-center justify-between gap-2 border-b border-border-strong pb-2.5">
        <h2 className="font-serif text-base font-semibold text-foreground">{title}</h2>
        {seeAllHref ? (
          <Link href={seeAllHref} className="shrink-0 text-xs font-medium text-accent hover:underline">
            {seeAllLabel}
          </Link>
        ) : null}
      </div>

      <ol className="mt-3 space-y-3">
        {leadImage && lead.imageUrl ? (
          <li>
            <Link href={`/article/${lead.id}`} className="group/link block">
              <ArticleImage src={lead.imageUrl} className="block aspect-[16/9] rounded-lg" />
              <h3 className="mt-2 text-sm font-semibold leading-snug text-foreground transition-colors group-hover/link:text-accent">
                {lead.title}
              </h3>
              <p className="mt-1 text-[11px] text-muted-foreground">
                {lead.source} · {timeAgo(lead.publishedAt, lang)}
              </p>
            </Link>
          </li>
        ) : (
          <HeadlineRow item={lead} index={1} numbered={numbered} lang={lang} />
        )}
        {rest.map((item, i) => (
          <HeadlineRow key={item.id} item={item} index={i + 2} numbered={numbered} lang={lang} />
        ))}
      </ol>
    </section>
  );
}

function HeadlineRow({
  item,
  index,
  numbered,
  lang,
}: {
  item: NewsItem;
  index: number;
  numbered: boolean;
  lang: PortalLanguage;
}) {
  return (
    <li className="flex gap-2.5">
      {numbered ? (
        <span className="w-4 shrink-0 font-serif text-lg font-semibold leading-none text-border-strong">
          {index}
        </span>
      ) : null}
      <Link href={`/article/${item.id}`} className="group/link min-w-0">
        <h3 className="text-sm font-semibold leading-snug text-foreground transition-colors group-hover/link:text-accent">
          {item.title}
        </h3>
        <p className="mt-1 text-[11px] text-muted-foreground">
          {item.source} · {timeAgo(item.publishedAt, lang)}
        </p>
      </Link>
    </li>
  );
}
