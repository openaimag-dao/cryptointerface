"use client";

import { Search, LogOut, Settings, UserRound } from "lucide-react";

import { useUtcClock } from "@/hooks/use-utc-clock";
import { useConnectionStore } from "@/store/connection-store";
import { Input } from "@/components/ui/input";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { ConnectionStatusIndicator } from "@/components/layout/connection-status";

export function Header() {
  const utcTime = useUtcClock();
  const apiStatus = useConnectionStore((state) => state.apiStatus);
  const wsStatus = useConnectionStore((state) => state.wsStatus);

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-border-subtle bg-background/80 px-6 backdrop-blur-xl">
      <div className="relative w-full max-w-sm">
        <Search className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Search markets, symbols, signals..."
          className="pl-9"
        />
      </div>

      <div className="ml-auto flex items-center gap-2.5">
        <div className="hidden items-center gap-2 rounded-md border border-border-subtle bg-white/[0.02] px-2.5 py-1.5 font-tabular text-xs text-muted-foreground md:flex">
          <span className="text-muted-foreground">UTC</span>
          <span className="text-foreground">{utcTime ?? "--:--:--"}</span>
        </div>

        <ConnectionStatusIndicator label="API" status={apiStatus} />
        <ConnectionStatusIndicator label="WS" status={wsStatus} />

        <ThemeToggle />

        <DropdownMenu>
          <DropdownMenuTrigger className="rounded-full outline-none ring-offset-2 focus-visible:ring-2 focus-visible:ring-accent/50">
            <Avatar>
              <AvatarFallback>AM</AvatarFallback>
            </Avatar>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>AIMAG Trader</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <UserRound className="size-4" />
              Profile
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Settings className="size-4" />
              Settings
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <LogOut className="size-4" />
              Sign out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
