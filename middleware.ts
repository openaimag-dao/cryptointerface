import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";

export async function middleware(request: NextRequest): Promise<NextResponse> {
  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  // Fail closed: no cookie, an invalid one, or JWT_SECRET_KEY unset all
  // resolve to "not authenticated" — never fall through to the terminal.
  const session = token ? await verifySessionToken(token) : null;

  if (!session) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", request.nextUrl.pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Editorial workflow admin pages need role="admin" on top of a valid
  // session. This is a UX-layer gate only — every /api/admin/* call is
  // independently re-checked against the DB-persisted role by the backend
  // (app/api/deps.py::get_current_admin_user), so a stale JWT can never
  // grant real admin access even if it slips past this check.
  if (request.nextUrl.pathname.startsWith("/admin") && session.role !== "admin") {
    return NextResponse.redirect(new URL("/", request.url));
  }

  return NextResponse.next();
}

// The terminal/dashboard is a private tool, not part of the public news
// portal. Route groups like (terminal) don't appear in the URL, so the
// protected paths are listed explicitly here — this must stay in sync with
// app/(terminal)'s subdirectories. Next.js statically analyzes this config
// at build time, so the matcher has to be a literal array (no .map(), no
// separate identifier reference).
export const config = {
  matcher: [
    "/dashboard/:path*",
    "/ai-chat/:path*",
    "/assets/:path*",
    "/backtesting/:path*",
    "/liquidations/:path*",
    "/macro/:path*",
    "/markets/:path*",
    "/news/:path*",
    "/portfolio/:path*",
    "/sentiment/:path*",
    "/settings/:path*",
    "/signals/:path*",
    "/whales/:path*",
    "/saved/:path*",
    "/watchlist/:path*",
    "/account/:path*",
    "/admin/:path*",
  ],
};
