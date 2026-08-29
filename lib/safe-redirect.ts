/**
 * Guards a caller-supplied "where to go next" path against open-redirect
 * abuse — must be a same-site relative path, never an absolute or
 * protocol-relative URL (e.g. "//evil.com", which the browser still
 * treats as an external redirect).
 */
export function isSafeRedirectPath(path: string | undefined | null): path is string {
  return !!path && path.startsWith("/") && !path.startsWith("//");
}
