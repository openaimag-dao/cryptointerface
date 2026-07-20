import { PageHeader } from "@/components/common/page-header";
import { PortfolioSummary } from "@/components/portfolio/portfolio-summary";
import { PositionsTable } from "@/components/portfolio/positions-table";
import { HistoryTable } from "@/components/portfolio/history-table";

export default function PortfolioPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Portfolio" description="Track balances, open exposure, and historical performance" />
      <PortfolioSummary />
      <PositionsTable />
      <HistoryTable />
    </div>
  );
}
