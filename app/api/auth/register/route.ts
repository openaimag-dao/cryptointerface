import type { NextRequest } from "next/server";

import { proxyAuthRequest } from "@/lib/backend-auth-proxy";

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => ({}));
  return proxyAuthRequest("/api/auth/register", body);
}
