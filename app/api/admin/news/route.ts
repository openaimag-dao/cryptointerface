import type { NextRequest } from "next/server";

import { proxyAuthenticatedRequest } from "@/lib/backend-user-proxy";

export async function GET(request: NextRequest) {
  const query = request.nextUrl.searchParams.toString();
  return proxyAuthenticatedRequest(`/api/admin/news${query ? `?${query}` : ""}`);
}
