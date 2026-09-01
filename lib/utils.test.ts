import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { isBreakingNews } from "./utils";

const NOW = new Date("2026-08-31T12:00:00Z");

describe("isBreakingNews", () => {
  beforeEach(() => vi.setSystemTime(NOW));
  afterEach(() => vi.useRealTimers());

  it("is true for a recent, high-impact article", () => {
    const publishedAt = new Date(NOW.getTime() - 30 * 60_000).toISOString(); // 30min ago
    expect(isBreakingNews(publishedAt, 75)).toBe(true);
  });

  it("is false once the article ages past the window, even at max impact", () => {
    const publishedAt = new Date(NOW.getTime() - 3 * 60 * 60_000).toISOString(); // 3h ago
    expect(isBreakingNews(publishedAt, 100)).toBe(false);
  });

  it("is false for a recent article below the impact threshold", () => {
    const publishedAt = new Date(NOW.getTime() - 5 * 60_000).toISOString(); // 5min ago
    expect(isBreakingNews(publishedAt, 45)).toBe(false);
  });

  it("is false for a future-dated timestamp (clock skew), not a crash or a false positive", () => {
    const publishedAt = new Date(NOW.getTime() + 60_000).toISOString(); // 1min in the future
    expect(isBreakingNews(publishedAt, 90)).toBe(false);
  });
});
