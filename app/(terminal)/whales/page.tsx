import { PageHeader } from "@/components/common/page-header";
import { WhaleSummary } from "@/components/whales/whale-summary";
import { WhaleTransactionsTable } from "@/components/whales/whale-transactions-table";

export default function WhalesPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Whale Tracker" description="Large on-chain movements and exchange flows in real time" />
      <WhaleSummary />
      <WhaleTransactionsTable />
    </div>
  );
}
