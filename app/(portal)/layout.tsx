import type { ReactNode } from "react";
import Link from "next/link";
import { cookies } from "next/headers";

import { PORTAL_TOPICS } from "@/lib/portal-topics";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";

export default async function PortalLayout({ children }: { children: ReactNode }) {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;
  const today = new Date().toLocaleDateString("en-US", { weekday: "long", month: "long", day: "numeric" });

  return (
    <div className="portal-theme flex min-h-screen flex-col bg-background text-foreground">
      <header className="border-b border-border-strong">
        {/* Utility bar: date + account, small and out of the way — a
            masthead detail, not the focal point. */}
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-2 text-xs text-muted-foreground">
          <span>{today}</span>
          <div className="flex items-center gap-4">
            <Link href="/dashboard" className="transition-colors hover:text-foreground">
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
          </div>
        </div>
        <div className="border-t border-border-subtle">
          {/* Wordmark: serif, centered — the masthead. */}
          <div className="mx-auto max-w-6xl px-6 py-6 text-center">
            <Link href="/" className="font-serif text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
              AIMAG <span className="text-accent">News</span>
            </Link>
            <p className="mt-1 text-xs uppercase tracking-[0.2em] text-muted-foreground">
              Crypto · AI · Blockchain · Innovation
            </p>
          </div>
        </div>
        <nav className="border-t border-border-strong">
          <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-center gap-x-6 gap-y-2 px-6 py-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            {PORTAL_TOPICS.map((topic) => (
              <Link key={topic.slug} href={`/category/${topic.slug}`} className="transition-colors hover:text-accent">
                {topic.label}
              </Link>
            ))}
            <Link href="/trending" className="transition-colors hover:text-accent">
              Trending
            </Link>
            <Link href="/search" className="transition-colors hover:text-accent">
              Search
            </Link>
          </div>
        </nav>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-10">{children}</main>
      <footer className="border-t border-border-strong px-6 py-8 text-center text-xs text-muted-foreground">
        <p className="font-serif text-sm text-foreground">AIMAG News</p>
        <p className="mt-2">
          Crypto, AI, Blockchain &amp; Innovation headlines — aggregated from real sources and classified
          automatically. Every story links back to its original publisher.
        </p>
      </footer>
    </div>
  );
}
