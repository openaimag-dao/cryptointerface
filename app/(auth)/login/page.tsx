import type { Metadata } from "next";

import { LoginForm } from "@/components/auth/login-form";

export const metadata: Metadata = {
  title: "Sign in",
  robots: { index: false, follow: false },
};

interface LoginPageProps {
  searchParams: Promise<{ next?: string }>;
}

function isSafeRedirectPath(path: string | undefined): path is string {
  // Must be a same-site relative path — reject absolute/protocol-relative
  // URLs (e.g. "//evil.com") to avoid using this as an open redirect.
  return !!path && path.startsWith("/") && !path.startsWith("//");
}

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const { next } = await searchParams;
  return <LoginForm nextPath={isSafeRedirectPath(next) ? next : "/dashboard"} />;
}
