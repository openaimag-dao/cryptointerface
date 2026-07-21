"use client";

import { Sparkles } from "lucide-react";

import { useSignals } from "@/hooks/use-signals";
import { Skeleton } from "@/components/ui/skeleton";
import { SignalCard } from "@/components/signals/signal-card";

export function SignalGrid() {
  const { data: signals, isLoading } = useSignals();

  if (isLoading || !signals) {
    return (
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {Array.from({ length: 6 }).map((_, index) => (
          <Skeleton key={index} className="h-[360px] rounded-xl" />
        ))}
      </div>
    );
  }

  if (signals.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center gap-2 rounded-xl border border-border-subtle bg-white/[0.02] py-16 text-center">
        <Sparkles className="size-5 text-muted-foreground" />
        <p className="text-sm text-foreground">No high-conviction signals right now</p>
        <p className="max-w-sm text-xs text-muted-foreground">
          Every watchlist symbol is currently reading WAIT — the AI engine only surfaces a signal here once
          it&apos;s confident enough to call a direction. Check back shortly.
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
      {signals.map((signal, index) => (
        <SignalCard key={signal.id} signal={signal} index={index} />
      ))}
    </div>
  );
}
