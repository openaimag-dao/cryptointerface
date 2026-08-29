import type { MetadataRoute } from "next";

import { SITE_URL } from "@/lib/env";

// Kept in sync with middleware.ts's protected-path list. The terminal is
// already 401-gated by Basic Auth, so this is defense-in-depth rather than
// the only thing keeping crawlers out.
const TERMINAL_PATHS = [
  "/dashboard",
  "/ai-chat",
  "/assets",
  "/backtesting",
  "/liquidations",
  "/macro",
  "/markets",
  "/news",
  "/portfolio",
  "/sentiment",
  "/settings",
  "/signals",
  "/whales",
];

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/search", ...TERMINAL_PATHS],
    },
    sitemap: `${SITE_URL}/sitemap.xml`,
  };
}
