import type { Metadata } from "next";
import type { ReactNode } from "react";

import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { MarketSocketProvider } from "@/components/layout/market-socket-provider";

// Overrides the root layout's portal-oriented metadata (title template,
// OpenGraph) for the private terminal — it's gated by middleware.ts's Basic
// Auth and has nothing to do with the public news portal's branding or SEO.
export const metadata: Metadata = {
  // `absolute` breaks out of the root layout's "%s | AIMAG News" template —
  // without it, Next.js would wrap this segment's own default title in the
  // parent's template too, producing "AIMAG AI Terminal | AIMAG News".
  title: { absolute: "AIMAG AI Terminal", default: "AIMAG AI Terminal", template: "%s | AIMAG AI Terminal" },
  description: "Professional AI-powered crypto trading terminal",
  robots: { index: false, follow: false },
};

export default function TerminalLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen bg-background">
      <MarketSocketProvider />
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header />
        <main className="flex-1 px-6 py-6">{children}</main>
      </div>
    </div>
  );
}
