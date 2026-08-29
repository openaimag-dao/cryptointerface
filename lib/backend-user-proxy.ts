import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { API_BASE_URL } from "@/lib/env";
import { SESSION_COOKIE_NAME } from "@/lib/session";

/**
 * Forwards a request to a `get_current_user`-protected backend endpoint,
 * converting the frontend's own httpOnly session cookie into the
 * `Authorization: Bearer` header the backend actually checks (see
 * backend/app/api/deps.py) — the browser never sees or sends the raw
 * token itself, only this first-party cookie.
 */
export async function proxyAuthenticatedRequest(path: string, init: RequestInit = {}): Promise<NextResponse> {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  if (!token) {
    return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
  }

  const backendResponse = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { ...init.headers, Authorization: `Bearer ${token}` },
    cache: "no-store",
  });

  if (backendResponse.status === 204) {
    return new NextResponse(null, { status: 204 });
  }

  const data = await backendResponse.json().catch(() => null);
  return NextResponse.json(data, { status: backendResponse.status });
}
