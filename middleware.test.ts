// @vitest-environment node
// jose's webapi build does `instanceof Uint8Array` on the signing key;
// jsdom's global Uint8Array is a different realm's constructor than
// Node's, which TextEncoder().encode() here produces — cross-realm
// instanceof fails even though the bytes are identical. Middleware logic
// has no DOM dependency anyway, so run this file under plain Node.
import { SignJWT } from "jose";
import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { config, middleware } from "./middleware";
import { SESSION_COOKIE_NAME } from "./lib/session";

const TEST_SECRET = "test-secret-key-for-middleware-tests";

function requestFor(path: string, cookieValue?: string): NextRequest {
  const headers = new Headers();
  if (cookieValue) headers.set("cookie", `${SESSION_COOKIE_NAME}=${cookieValue}`);
  return new NextRequest(new URL(path, "https://portal.example.com"), { headers });
}

async function signSessionToken(payload: { sub: string; role: string }, secret = TEST_SECRET): Promise<string> {
  const key = new TextEncoder().encode(secret);
  return new SignJWT(payload).setProtectedHeader({ alg: "HS256" }).setIssuedAt().setExpirationTime("7d").sign(key);
}

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("middleware", () => {
  it("redirects to /login with no session cookie (fails closed)", async () => {
    vi.stubEnv("JWT_SECRET_KEY", TEST_SECRET);

    const response = await middleware(requestFor("/dashboard"));

    expect(response.status).toBe(307);
    const location = new URL(response.headers.get("location")!);
    expect(location.pathname).toBe("/login");
    expect(location.searchParams.get("next")).toBe("/dashboard");
  });

  it("redirects to /login when JWT_SECRET_KEY isn't configured, even with a well-formed token", async () => {
    vi.stubEnv("JWT_SECRET_KEY", "");
    const token = await signSessionToken({ sub: "1", role: "user" });

    const response = await middleware(requestFor("/dashboard", token));

    expect(response.status).toBe(307);
  });

  it("redirects to /login for a tampered token", async () => {
    vi.stubEnv("JWT_SECRET_KEY", TEST_SECRET);
    const token = await signSessionToken({ sub: "1", role: "user" });
    // Flip a character in the middle of the signature segment — flipping
    // the very last base64url character can decode to the same bytes
    // (trailing padding bits), so this is the reliable way to corrupt it.
    const midpoint = Math.floor(token.length / 2);
    const flipped = token[midpoint] === "a" ? "b" : "a";
    const tampered = token.slice(0, midpoint) + flipped + token.slice(midpoint + 1);

    const response = await middleware(requestFor("/dashboard", tampered));

    expect(response.status).toBe(307);
  });

  it("redirects to /login for a token signed with the wrong secret", async () => {
    vi.stubEnv("JWT_SECRET_KEY", TEST_SECRET);
    const token = await signSessionToken({ sub: "1", role: "user" }, "wrong-secret");

    const response = await middleware(requestFor("/dashboard", token));

    expect(response.status).toBe(307);
  });

  it("allows a protected path with a valid session cookie", async () => {
    vi.stubEnv("JWT_SECRET_KEY", TEST_SECRET);
    const token = await signSessionToken({ sub: "1", role: "user" });

    const response = await middleware(requestFor("/dashboard", token));

    expect(response.status).toBe(200);
  });

  it("redirects a non-admin session away from /admin", async () => {
    vi.stubEnv("JWT_SECRET_KEY", TEST_SECRET);
    const token = await signSessionToken({ sub: "1", role: "user" });

    const response = await middleware(requestFor("/admin/news", token));

    expect(response.status).toBe(307);
    const location = new URL(response.headers.get("location")!);
    expect(location.pathname).toBe("/");
  });

  it("allows an admin session into /admin", async () => {
    vi.stubEnv("JWT_SECRET_KEY", TEST_SECRET);
    const token = await signSessionToken({ sub: "1", role: "admin" });

    const response = await middleware(requestFor("/admin/news", token));

    expect(response.status).toBe(200);
  });

  it("redirects to /login for /admin with no session at all (fails closed, not just non-admin)", async () => {
    vi.stubEnv("JWT_SECRET_KEY", TEST_SECRET);

    const response = await middleware(requestFor("/admin/news"));

    expect(response.status).toBe(307);
    const location = new URL(response.headers.get("location")!);
    expect(location.pathname).toBe("/login");
  });

  it("matcher covers every (terminal) and private-dashboard route but leaves the portal root free", () => {
    expect(config.matcher).toContain("/dashboard/:path*");
    expect(config.matcher).toContain("/whales/:path*");
    expect(config.matcher).toContain("/saved/:path*");
    expect(config.matcher).toContain("/watchlist/:path*");
    expect(config.matcher).toContain("/account/:path*");
    expect(config.matcher).toContain("/admin/:path*");
    expect(config.matcher).not.toContain("/:path*");
  });
});
