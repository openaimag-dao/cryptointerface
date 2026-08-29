import type { NextRequest } from "next/server";

import { proxyAuthenticatedRequest } from "@/lib/backend-user-proxy";

export async function GET() {
  return proxyAuthenticatedRequest("/api/user/watchlist");
}

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => ({}));
  return proxyAuthenticatedRequest("/api/user/watchlist", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}
