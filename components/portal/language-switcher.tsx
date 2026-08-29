"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";

import { cn } from "@/lib/utils";
import { PORTAL_LANGUAGES, type PortalLanguage } from "@/lib/portal-i18n";

export function LanguageSwitcher({ current }: { current: PortalLanguage }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const query = searchParams.toString();
  const currentPath = query ? `${pathname}?${query}` : pathname;

  return (
    <div className="flex items-center gap-1">
      {PORTAL_LANGUAGES.map((lang) => (
        <Link
          key={lang.code}
          href={`/api/locale?lang=${lang.code}&next=${encodeURIComponent(currentPath)}`}
          className={cn(
            "rounded px-1.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide transition-colors",
            lang.code === current ? "bg-accent-dim text-accent" : "text-muted-foreground hover:text-foreground",
          )}
        >
          {lang.label}
        </Link>
      ))}
    </div>
  );
}
