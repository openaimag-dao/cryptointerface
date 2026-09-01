import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { PORTAL_THEME_COOKIE, resolvePortalTheme } from "@/lib/portal-theme";
import { isSafeRedirectPath } from "@/lib/safe-redirect";

const ONE_YEAR_SECONDS = 60 * 60 * 24 * 365;

/**
 * Sets the portal's theme cookie and redirects back — same shape as
 * /api/locale and for the same reason: the pages reading this cookie are
 * Server Components, so a plain link + real navigation avoids any
 * light/dark flash a client-side toggle would otherwise cause.
 */
export async function GET(request: NextRequest) {
  const theme = resolvePortalTheme(request.nextUrl.searchParams.get("theme") ?? undefined);
  const next = request.nextUrl.searchParams.get("next");
  const destination = isSafeRedirectPath(next) ? next : "/";

  const response = NextResponse.redirect(new URL(destination, request.url));
  response.cookies.set(PORTAL_THEME_COOKIE, theme, { maxAge: ONE_YEAR_SECONDS, path: "/" });
  return response;
}
