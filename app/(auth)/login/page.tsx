import type { Metadata } from "next";

import { isSafeRedirectPath } from "@/lib/safe-redirect";
import { LoginForm } from "@/components/auth/login-form";

export const metadata: Metadata = {
  title: "Sign in",
  robots: { index: false, follow: false },
};

interface LoginPageProps {
  searchParams: Promise<{ next?: string }>;
}

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const { next } = await searchParams;
  return <LoginForm nextPath={isSafeRedirectPath(next) ? next : "/dashboard"} />;
}
