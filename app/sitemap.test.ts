import { afterEach, describe, expect, it, vi } from "vitest";

import sitemap from "@/app/sitemap";
import type { NewsItem, PortalNewsPage } from "@/types";

function makeItem(id: number): NewsItem {
  return {
    id: String(id),
    source: "Test Source",
    title: `Title ${id}`,
    summary: "Summary",
    publishedAt: "2026-01-01T00:00:00.000Z",
    language: "en",
    symbols: [],
    url: "https://example.com",
    impactScore: 50,
    sentiment: "NEUTRAL",
    category: "Market",
    portalTopic: "CRYPTO",
  };
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("sitemap", () => {
  it("includes every static portal route and paginates through recent articles", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = new URL(String(input));
      const offset = Number(url.searchParams.get("offset") ?? "0");
      const items =
        offset === 0
          ? Array.from({ length: 100 }, (_, i) => makeItem(i))
          : Array.from({ length: 50 }, (_, i) => makeItem(100 + i));
      const page: PortalNewsPage = { items, total: 150, limit: 100, offset };
      return new Response(JSON.stringify(page), { status: 200 });
    });
    vi.stubGlobal("fetch", fetchMock);

    const entries = await sitemap();
    const staticUrls = entries.filter((entry) => !entry.url.includes("/article/")).map((entry) => entry.url);

    expect(staticUrls.some((url) => url.endsWith("/category/crypto"))).toBe(true);
    expect(staticUrls.some((url) => url.endsWith("/category/ai"))).toBe(true);
    expect(staticUrls.some((url) => url.endsWith("/category/blockchain"))).toBe(true);
    expect(staticUrls.some((url) => url.endsWith("/category/innovation"))).toBe(true);
    expect(staticUrls.some((url) => url.endsWith("/search"))).toBe(true);
    expect(staticUrls.some((url) => url.endsWith("/trending"))).toBe(true);

    const articleEntries = entries.filter((entry) => entry.url.includes("/article/"));
    expect(articleEntries).toHaveLength(150);
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("stops after a short page and still returns the static entries when there are no articles", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ items: [], total: 0, limit: 100, offset: 0 }), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const entries = await sitemap();

    expect(entries.filter((entry) => entry.url.includes("/article/"))).toHaveLength(0);
    expect(entries.length).toBeGreaterThan(0);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("caps article entries at 300 even if more pages are available", async () => {
    const fetchMock = vi.fn(async (input: RequestInfo | URL) => {
      const url = new URL(String(input));
      const offset = Number(url.searchParams.get("offset") ?? "0");
      const items = Array.from({ length: 100 }, (_, i) => makeItem(offset + i));
      const page: PortalNewsPage = { items, total: 1000, limit: 100, offset };
      return new Response(JSON.stringify(page), { status: 200 });
    });
    vi.stubGlobal("fetch", fetchMock);

    const entries = await sitemap();
    const articleEntries = entries.filter((entry) => entry.url.includes("/article/"));

    expect(articleEntries).toHaveLength(300);
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });
});
