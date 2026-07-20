import { PageHeader } from "@/components/common/page-header";
import { MacroIndicatorsGrid } from "@/components/macro/macro-indicators-grid";
import { MacroEventsList } from "@/components/macro/macro-events-list";

export default function MacroPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Macro" description="Global macroeconomic conditions shaping crypto market cycles" />
      <MacroIndicatorsGrid />
      <MacroEventsList />
    </div>
  );
}
