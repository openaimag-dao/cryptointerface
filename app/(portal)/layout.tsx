import type { ReactNode } from "react";
import Link from "next/link";
import { cookies } from "next/headers";

import { PORTAL_TOPICS } from "@/lib/portal-topics";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";

export default async function PortalLayout({ children }: { children: ReactNode }) {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="border-b border-border-strong">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-4">
          <Link href="/" className="text-lg font-semibold tracking-tight text-foreground">
            AIMAG News
          </Link>
          <nav className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
            {PORTAL_TOPICS.map((topic) => (
              <Link
                key={topic.slug}
                href={`/category/${topic.slug}`}
                className="transition-colors hover:text-foreground"
              >
                {topic.label}
              </Link>
            ))}
            <Link href="/trending" className="transition-colors hover:text-foreground">
              Trending
            </Link>
            <Link href="/search" className="transition-colors hover:text-foreground">
              Search
            </Link>
            <Link href="/dashboard" className="text-xs text-muted-foreground/70 transition-colors hover:text-foreground">
              Terminal ↗
            </Link>
            {session ? (
              <Link href="/account" className="transition-colors hover:text-foreground">
                Account
              </Link>
            ) : (
              <Link href="/login" className="transition-colors hover:text-foreground">
                Sign in
              </Link>
            )}
          </nav>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-8">{children}</main>
      <footer className="border-t border-border-strong px-6 py-6 text-center text-xs text-muted-foreground">
        AIMAG News — Crypto, AI, Blockchain &amp; Innovation headlines, aggregated and classified automatically.
      </footer>
    </div>
  );
}
