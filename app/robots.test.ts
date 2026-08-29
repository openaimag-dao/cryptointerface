import { describe, expect, it } from "vitest";

import robots from "@/app/robots";

describe("robots", () => {
  it("disallows /search and every (terminal) route, and points at the sitemap", () => {
    const result = robots();
    const rules = Array.isArray(result.rules) ? result.rules[0] : result.rules;

    expect(rules.disallow).toContain("/search");
    expect(rules.disallow).toContain("/dashboard");
    expect(rules.disallow).toContain("/whales");
    expect(rules.allow).toBe("/");
    expect(result.sitemap).toContain("/sitemap.xml");
  });
});
