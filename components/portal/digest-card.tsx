import { Sparkles } from "lucide-react";

import { timeAgo } from "@/lib/utils";
import { portalStrings, type PortalLanguage } from "@/lib/portal-i18n";
import type { NewsDigest } from "@/types";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

export function DigestCard({ digest, lang = "en" }: { digest: NewsDigest; lang?: PortalLanguage }) {
  const t = portalStrings(lang);
  return (
    <Card className="border-accent/20 bg-accent-dim/40">
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
        <span className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-accent">
          <Sparkles className="size-3.5" />
          {t.digestLabel}
        </span>
        <span className="text-xs text-muted-foreground">
          {t.digestFrom(digest.articleCount)} · {timeAgo(digest.generatedAt, lang)}
        </span>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="text-sm leading-relaxed text-foreground">{digest.summary}</p>
        {digest.highlights.length > 0 ? (
          <ul className="mt-3 space-y-1.5">
            {digest.highlights.map((highlight, index) => (
              <li key={index} className="flex gap-2 text-xs text-muted-foreground">
                <span className="text-accent">•</span>
                {highlight}
              </li>
            ))}
          </ul>
        ) : null}
      </CardContent>
    </Card>
  );
}
