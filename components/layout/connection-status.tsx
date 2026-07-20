"use client";

import { cn } from "@/lib/utils";
import type { ConnectionStatus } from "@/store/connection-store";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

const STATUS_CONFIG: Record<ConnectionStatus, { color: string; label: string }> = {
  online: { color: "bg-accent shadow-[0_0_8px_rgba(0,230,118,0.8)]", label: "Connected" },
  connecting: { color: "bg-warning animate-pulse", label: "Connecting" },
  offline: { color: "bg-danger", label: "Offline" },
};

interface ConnectionStatusProps {
  label: string;
  status: ConnectionStatus;
}

export function ConnectionStatusIndicator({ label, status }: ConnectionStatusProps) {
  const config = STATUS_CONFIG[status];

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div className="flex items-center gap-1.5 rounded-md border border-border-subtle bg-white/[0.02] px-2.5 py-1.5">
          <span className={cn("size-1.5 rounded-full", config.color)} />
          <span className="hidden text-xs font-medium text-muted-foreground sm:inline">{label}</span>
        </div>
      </TooltipTrigger>
      <TooltipContent side="bottom">
        {label}: {config.label}
      </TooltipContent>
    </Tooltip>
  );
}
