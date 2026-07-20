import { PageHeader } from "@/components/common/page-header";
import { LiquidationTotals } from "@/components/liquidations/liquidation-totals";
import { LiquidationHeatmap } from "@/components/liquidations/liquidation-heatmap";
import { LiquidationsTable } from "@/components/liquidations/liquidations-table";

export default function LiquidationsPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Liquidations" description="Forced closures across major exchanges and derivatives venues" />
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[320px_1fr]">
        <LiquidationTotals />
        <LiquidationHeatmap />
      </div>
      <LiquidationsTable />
    </div>
  );
}
