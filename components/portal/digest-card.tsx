import { Sparkles } from "lucide-react";

import { timeAgo } from "@/lib/utils";
import type { NewsDigest } from "@/types";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

export function DigestCard({ digest }: { digest: NewsDigest }) {
  return (
    <Card className="border-accent/20 bg-accent-dim/40">
      <CardHeader className="flex-row items-center justify-between space-y-0 pb-2">
        <span className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-accent">
          <Sparkles className="size-3.5" />
          AI Digest
        </span>
        <span className="text-xs text-muted-foreground">
          From {digest.articleCount} articles · {timeAgo(digest.generatedAt)}
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
