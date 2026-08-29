import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

// The terminal/dashboard is a private tool, not part of the public news
// portal. Route groups like (terminal) don't appear in the URL, so the
// protected paths are listed explicitly here — this must stay in sync with
// app/(terminal)'s subdirectories.
const PROTECTED_PATH_PREFIXES = [
  "/dashboard",
  "/ai-chat",
  "/assets",
  "/backtesting",
  "/liquidations",
  "/macro",
  "/markets",
  "/news",
  "/portfolio",
  "/sentiment",
  "/settings",
  "/signals",
  "/whales",
];

function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let mismatch = 0;
  for (let i = 0; i < a.length; i++) {
    mismatch |= a.charCodeAt(i) ^ b.charCodeAt(i);
  }
  return mismatch === 0;
}

function unauthorized(): NextResponse {
  return new NextResponse("Authentication required", {
    status: 401,
    headers: {
      "WWW-Authenticate": 'Basic realm="AIMAG Terminal", charset="UTF-8"',
    },
  });
}

export function middleware(request: NextRequest): NextResponse {
  const expectedUser = process.env.TERMINAL_BASIC_AUTH_USER;
  const expectedPassword = process.env.TERMINAL_BASIC_AUTH_PASSWORD;

  // Fail closed: the terminal has no other access control, so if credentials
  // aren't configured there is no safe way to grant access — block instead
  // of leaving it open.
  if (!expectedUser || !expectedPassword) {
    return unauthorized();
  }

  const authHeader = request.headers.get("authorization");
  if (!authHeader?.startsWith("Basic ")) {
    return unauthorized();
  }

  let decoded: string;
  try {
    decoded = atob(authHeader.slice("Basic ".length));
  } catch {
    return unauthorized();
  }

  const separatorIndex = decoded.indexOf(":");
  if (separatorIndex === -1) {
    return unauthorized();
  }

  const user = decoded.slice(0, separatorIndex);
  const password = decoded.slice(separatorIndex + 1);

  if (!timingSafeEqual(user, expectedUser) || !timingSafeEqual(password, expectedPassword)) {
    return unauthorized();
  }

  return NextResponse.next();
}

export const config = {
  matcher: PROTECTED_PATH_PREFIXES.map((prefix) => `${prefix}/:path*`),
};
