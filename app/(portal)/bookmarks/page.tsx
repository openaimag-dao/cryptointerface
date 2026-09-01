import type { Metadata } from "next";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";

import { PageHeader } from "@/components/common/page-header";
import { SavedArticlesGrid } from "@/components/portal/saved-articles-grid";
import { PORTAL_LANGUAGE_COOKIE, portalStrings, resolvePortalLanguage } from "@/lib/portal-i18n";
import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";

export const metadata: Metadata = {
  title: "Saved Articles",
  robots: { index: false, follow: false },
};

export default async function SavedPage() {
  const cookieStore = await cookies();
  const token = cookieStore.get(SESSION_COOKIE_NAME)?.value;
  const session = token ? await verifySessionToken(token) : null;
  if (!session) redirect("/login?next=/bookmarks");

  const lang = resolvePortalLanguage(cookieStore.get(PORTAL_LANGUAGE_COOKIE)?.value);
  const t = portalStrings(lang);

  return (
    <div className="space-y-8">
      <PageHeader title={t.savedTitle} description={t.savedDescription} serif />
      <SavedArticlesGrid lang={lang} />
    </div>
  );
}
