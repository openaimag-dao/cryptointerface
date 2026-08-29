import type { ReactNode } from "react";
import Link from "next/link";

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background px-4">
      <Link href="/" className="mb-8 text-lg font-semibold tracking-tight text-foreground">
        AIMAG News
      </Link>
      <div className="w-full max-w-sm">{children}</div>
    </div>
  );
}
