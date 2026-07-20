import { PageHeader } from "@/components/common/page-header";
import { MarketsTable } from "@/components/markets/markets-table";

export default function MarketsPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Markets" description="Live pricing, derivatives data, and AI scoring across your universe" />
      <MarketsTable />
    </div>
  );
}
