import { proxyAuthenticatedRequest } from "@/lib/backend-user-proxy";

export async function POST(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return proxyAuthenticatedRequest(`/api/user/bookmarks/${id}`, { method: "POST" });
}

export async function DELETE(_request: Request, { params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return proxyAuthenticatedRequest(`/api/user/bookmarks/${id}`, { method: "DELETE" });
}
