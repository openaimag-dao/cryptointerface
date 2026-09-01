/**
 * The portal's own light/dark toggle — deliberately independent of the
 * trading terminal's next-themes setup (app/providers.tsx), the same way
 * portal-i18n.ts's language is its own cookie rather than tied to
 * anything else. The terminal defaults to dark; the portal must default
 * to its warm "premium editorial media" light look regardless of that,
 * so it can't just read the terminal's theme state.
 */
export type PortalTheme = "light" | "dark";

export const PORTAL_THEME_COOKIE = "portal_theme";
export const DEFAULT_PORTAL_THEME: PortalTheme = "light";

export function resolvePortalTheme(value: string | undefined): PortalTheme {
  return value === "dark" ? "dark" : DEFAULT_PORTAL_THEME;
}
