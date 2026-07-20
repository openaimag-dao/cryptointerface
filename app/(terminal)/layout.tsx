import type { ReactNode } from "react";

import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";

export default function TerminalLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header />
        <main className="flex-1 px-6 py-6">{children}</main>
      </div>
    </div>
  );
}
