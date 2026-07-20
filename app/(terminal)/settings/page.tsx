import { PageHeader } from "@/components/common/page-header";
import { AppearanceSettings, ApiSettings, NotificationSettings } from "@/components/settings/settings-sections";

export default function SettingsPage() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <PageHeader title="Settings" description="Manage your terminal preferences and integrations" />
      <AppearanceSettings />
      <NotificationSettings />
      <ApiSettings />
    </div>
  );
}
