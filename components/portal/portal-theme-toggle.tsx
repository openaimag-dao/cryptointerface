"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Moon, Sun } from "lucide-react";

import type { PortalTheme } from "@/lib/portal-theme";

export function PortalThemeToggle({ current }: { current: PortalTheme }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const query = searchParams.toString();
  const currentPath = query ? `${pathname}?${query}` : pathname;
  const target: PortalTheme = current === "dark" ? "light" : "dark";

  return (
    <Link
      href={`/api/portal-theme?theme=${target}&next=${encodeURIComponent(currentPath)}`}
      aria-label={target === "dark" ? "Switch to dark mode" : "Switch to light mode"}
      className="inline-flex size-6 items-center justify-center rounded text-muted-foreground transition-colors hover:text-foreground"
    >
      {current === "dark" ? <Sun className="size-3.5" /> : <Moon className="size-3.5" />}
    </Link>
  );
}
