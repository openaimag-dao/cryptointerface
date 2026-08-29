import { proxyAuthenticatedRequest } from "@/lib/backend-user-proxy";

export async function DELETE(_request: Request, { params }: { params: Promise<{ symbol: string }> }) {
  const { symbol } = await params;
  return proxyAuthenticatedRequest(`/api/user/watchlist/${symbol}`, { method: "DELETE" });
}
