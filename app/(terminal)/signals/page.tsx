import { PageHeader } from "@/components/common/page-header";
import { SignalGrid } from "@/components/signals/signal-grid";

export default function SignalsPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="AI Signals" description="High-conviction, AI-generated trade setups across your watchlist" />
      <SignalGrid />
    </div>
  );
}
