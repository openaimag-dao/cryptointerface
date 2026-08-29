import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";

import { config, middleware } from "./middleware";

function requestFor(path: string, authHeader?: string): NextRequest {
  const headers = new Headers();
  if (authHeader) headers.set("authorization", authHeader);
  return new NextRequest(new URL(path, "https://portal.example.com"), { headers });
}

function basicAuthHeader(user: string, password: string): string {
  return `Basic ${btoa(`${user}:${password}`)}`;
}

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("middleware", () => {
  it("blocks a protected path with no credentials configured (fails closed)", () => {
    vi.stubEnv("TERMINAL_BASIC_AUTH_USER", "");
    vi.stubEnv("TERMINAL_BASIC_AUTH_PASSWORD", "");

    const response = middleware(requestFor("/dashboard"));

    expect(response.status).toBe(401);
    expect(response.headers.get("WWW-Authenticate")).toContain("Basic");
  });

  it("blocks a protected path with no Authorization header", () => {
    vi.stubEnv("TERMINAL_BASIC_AUTH_USER", "admin");
    vi.stubEnv("TERMINAL_BASIC_AUTH_PASSWORD", "secret");

    const response = middleware(requestFor("/dashboard"));

    expect(response.status).toBe(401);
  });

  it("blocks a protected path with the wrong credentials", () => {
    vi.stubEnv("TERMINAL_BASIC_AUTH_USER", "admin");
    vi.stubEnv("TERMINAL_BASIC_AUTH_PASSWORD", "secret");

    const response = middleware(requestFor("/dashboard", basicAuthHeader("admin", "wrong")));

    expect(response.status).toBe(401);
  });

  it("blocks a malformed Authorization header", () => {
    vi.stubEnv("TERMINAL_BASIC_AUTH_USER", "admin");
    vi.stubEnv("TERMINAL_BASIC_AUTH_PASSWORD", "secret");

    const response = middleware(requestFor("/dashboard", "Basic not-valid-base64!!"));

    expect(response.status).toBe(401);
  });

  it("allows a protected path with the correct credentials", () => {
    vi.stubEnv("TERMINAL_BASIC_AUTH_USER", "admin");
    vi.stubEnv("TERMINAL_BASIC_AUTH_PASSWORD", "secret");

    const response = middleware(requestFor("/dashboard", basicAuthHeader("admin", "secret")));

    expect(response.status).toBe(200);
  });

  it("matcher covers every (terminal) route but leaves the portal root free", () => {
    expect(config.matcher).toContain("/dashboard/:path*");
    expect(config.matcher).toContain("/whales/:path*");
    expect(config.matcher).not.toContain("/:path*");
  });
});
