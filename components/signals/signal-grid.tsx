"use client";

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

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
      {signals.map((signal, index) => (
        <SignalCard key={signal.id} signal={signal} index={index} />
      ))}
    </div>
  );
}
