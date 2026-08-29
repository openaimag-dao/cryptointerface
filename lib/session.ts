import { jwtVerify } from "jose";

/**
 * Verifies the same HS256 JWT the backend issues on register/login
 * (see backend/app/services/auth_service.py) — JWT_SECRET_KEY must be
 * identical on both sides. Used by middleware.ts (Edge runtime) and the
 * /api/auth/* and /api/user/* Route Handlers (Node runtime); `jose` works
 * in both, unlike Node-only JWT libraries.
 */

export interface SessionPayload {
  userId: string;
  role: string;
}

export const SESSION_COOKIE_NAME = "session";
// Matches the backend's JWT_EXPIRE_MINUTES default (10080 min = 7 days) —
// see backend/.env.example. The cookie's own lifetime doesn't need to be
// exact: an expired JWT still fails verification even if the cookie outlives it.
export const SESSION_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 7;

function getSecretKey(): Uint8Array | null {
  const secret = process.env.JWT_SECRET_KEY;
  if (!secret) return null;
  return new TextEncoder().encode(secret);
}

export async function verifySessionToken(token: string): Promise<SessionPayload | null> {
  const key = getSecretKey();
  if (!key) return null;

  try {
    const { payload } = await jwtVerify(token, key);
    if (typeof payload.sub !== "string" || typeof payload.role !== "string") return null;
    return { userId: payload.sub, role: payload.role };
  } catch {
    return null;
  }
}
