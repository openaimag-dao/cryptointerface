import { proxyAuthenticatedRequest } from "@/lib/backend-user-proxy";

export async function GET() {
  return proxyAuthenticatedRequest("/api/admin/sources");
}
