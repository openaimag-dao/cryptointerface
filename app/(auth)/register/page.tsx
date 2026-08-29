import type { Metadata } from "next";

import { RegisterForm } from "@/components/auth/register-form";

export const metadata: Metadata = {
  title: "Register",
  robots: { index: false, follow: false },
};

interface RegisterPageProps {
  searchParams: Promise<{ next?: string }>;
}

function isSafeRedirectPath(path: string | undefined): path is string {
  return !!path && path.startsWith("/") && !path.startsWith("//");
}

export default async function RegisterPage({ searchParams }: RegisterPageProps) {
  const { next } = await searchParams;
  return <RegisterForm nextPath={isSafeRedirectPath(next) ? next : "/dashboard"} />;
}
