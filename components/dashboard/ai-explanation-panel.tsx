"use client";

import { AlertTriangle, Lightbulb, ListChecks, Sparkles, Tags } from "lucide-react";

import { useLlmExplanation } from "@/hooks/use-llm-explanation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Separator } from "@/components/ui/separator";

interface AiExplanationPanelProps {
  symbol: string;
}

function Section({ icon: Icon, title, items }: { icon: typeof ListChecks; title: string; items: string[] }) {
  if (items.length === 0) return null;
  return (
    <div>
      <p className="mb-2 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wider text-muted-foreground">
        <Icon className="size-3.5" />
        {title}
      </p>
      <ul className="space-y-1.5">
        {items.map((item) => (
          <li key={item} className="text-xs leading-relaxed text-foreground/90">
            • {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function AiExplanationPanel({ symbol }: AiExplanationPanelProps) {
  const { data: explanation, isLoading } = useLlmExplanation(symbol);

  return (
    <Card className="flex h-full flex-col">
      <CardHeader className="flex-row items-center justify-between space-y-0">
        <CardTitle className="flex items-center gap-1.5 text-foreground">
          <Sparkles className="size-4 text-accent" />
          AI Explanation
        </CardTitle>
        <span className="text-xs text-muted-foreground">{symbol}</span>
      </CardHeader>
      <CardContent className="flex-1 space-y-4">
        {isLoading || !explanation ? (
          <Skeleton className="h-40 w-full rounded-lg" />
        ) : (
          <>
            <p className="text-sm leading-relaxed text-foreground/90">{explanation.summary}</p>
            <p className="font-tabular text-xs text-muted-foreground">
              Confidence <span className="text-foreground">{Math.round(explanation.confidence)}%</span>
            </p>

            <Separator />

            <Section icon={ListChecks} title="Key Drivers" items={explanation.keyDrivers} />
            <Section icon={AlertTriangle} title="Risks" items={explanation.risks} />
            <Section icon={Lightbulb} title="Opportunities" items={explanation.opportunities} />
            <Section icon={Tags} title="Assets Affected" items={explanation.assetsAffected} />
          </>
        )}
      </CardContent>
    </Card>
  );
}
