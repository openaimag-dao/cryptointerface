import { PageHeader } from "@/components/common/page-header";
import { BacktestRunner } from "@/components/backtesting/backtest-runner";

export default function BacktestingPage() {
  return (
    <div className="space-y-6">
      <PageHeader title="Backtesting" description="Simulate AI strategy performance across historical conditions" />
      <BacktestRunner />
    </div>
  );
}
