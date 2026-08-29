import { NextResponse } from "next/server";

import { API_BASE_URL } from "@/lib/env";
import { SESSION_COOKIE_MAX_AGE_SECONDS, SESSION_COOKIE_NAME } from "@/lib/session";

/**
 * The backend and frontend are on separate domains (Railway/Vercel), so a
 * cookie set by the backend's response wouldn't be usable cross-origin.
 * register/login instead return the JWT in the JSON body; this proxies
 * that call and sets a first-party httpOnly cookie on the frontend's own
 * domain from the result — the only place the raw token exists client-side
 * is nowhere, since it never reaches the browser's JS.
 */
export async function proxyAuthRequest(path: "/api/auth/register" | "/api/auth/login", body: unknown) {
  const backendResponse = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
    cache: "no-store",
  });

  const data = await backendResponse.json().catch(() => null);
  if (!backendResponse.ok || !data?.accessToken) {
    return NextResponse.json(data ?? { detail: "Unexpected error" }, { status: backendResponse.status || 502 });
  }

  const response = NextResponse.json({ user: data.user }, { status: backendResponse.status });
  response.cookies.set(SESSION_COOKIE_NAME, data.accessToken, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: SESSION_COOKIE_MAX_AGE_SECONDS,
  });
  return response;
}
