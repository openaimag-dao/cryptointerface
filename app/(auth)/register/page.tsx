import type { Metadata } from "next";

import { isSafeRedirectPath } from "@/lib/safe-redirect";
import { RegisterForm } from "@/components/auth/register-form";

export const metadata: Metadata = {
  title: "Register",
  robots: { index: false, follow: false },
};

interface RegisterPageProps {
  searchParams: Promise<{ next?: string }>;
}

export default async function RegisterPage({ searchParams }: RegisterPageProps) {
  const { next } = await searchParams;
  return <RegisterForm nextPath={isSafeRedirectPath(next) ? next : "/dashboard"} />;
}
