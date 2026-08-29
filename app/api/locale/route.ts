import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { PORTAL_LANGUAGE_COOKIE, resolvePortalLanguage } from "@/lib/portal-i18n";
import { isSafeRedirectPath } from "@/lib/safe-redirect";

const ONE_YEAR_SECONDS = 60 * 60 * 24 * 365;

/**
 * Sets the portal's language cookie and redirects back to where the
 * reader was — the language switcher is plain `<Link>`s to this route
 * rather than a client-side fetch, since the pages that read the cookie
 * are Server Components and need a real navigation to re-render with it.
 */
export async function GET(request: NextRequest) {
  const lang = resolvePortalLanguage(request.nextUrl.searchParams.get("lang") ?? undefined);
  const next = request.nextUrl.searchParams.get("next");
  const destination = isSafeRedirectPath(next) ? next : "/";

  const response = NextResponse.redirect(new URL(destination, request.url));
  response.cookies.set(PORTAL_LANGUAGE_COOKIE, lang, { maxAge: ONE_YEAR_SECONDS, path: "/" });
  return response;
}
