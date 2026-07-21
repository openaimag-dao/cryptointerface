"use client";

import { useState } from "react";
import { PlayCircle } from "lucide-react";

import { CHART_TIMEFRAMES, WATCHLIST_SYMBOLS } from "@/lib/constants";
import { extractErrorDetail } from "@/services/backtest-service";
import { useBacktestEquity, useBacktestTrades, useRunBacktest } from "@/hooks/use-backtest";
import { BACKTEST_PERIOD_DAYS, type BacktestPeriodDays } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { BacktestSummaryCards } from "@/components/backtesting/summary-cards";
import { EquityCurveChart } from "@/components/backtesting/equity-curve-chart";
import { DrawdownChart } from "@/components/backtesting/drawdown-chart";
import { MonthlyReturnsChart } from "@/components/backtesting/monthly-returns-chart";
import { TradeDistributionChart } from "@/components/backtesting/trade-distribution-chart";
import { WinLossChart } from "@/components/backtesting/win-loss-chart";
import { TradeListTable } from "@/components/backtesting/trade-list-table";

export function BacktestRunner() {
  const [symbol, setSymbol] = useState(WATCHLIST_SYMBOLS[0]);
  const [timeframe, setTimeframe] = useState<(typeof CHART_TIMEFRAMES)[number]>("1h");
  const [periodDays, setPeriodDays] = useState<BacktestPeriodDays>(90);

  const { mutate, data: report, isPending, error } = useRunBacktest();
  const runId = report?.run.id;
  const { data: trades, isLoading: tradesLoading } = useBacktestTrades(runId);
  const { data: equity, isLoading: equityLoading } = useBacktestEquity(runId);

  function handleRun() {
    mutate({ symbol, timeframe, periodDays });
  }

  const isLoadingResults = isPending || (Boolean(runId) && (tradesLoading || equityLoading));

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-foreground">Configure Backtest</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap items-end gap-4">
          <SelectField label="Coin" value={symbol} onChange={setSymbol} options={WATCHLIST_SYMBOLS} />
          <SelectField
            label="Timeframe"
            value={timeframe}
            onChange={(value) => setTimeframe(value as (typeof CHART_TIMEFRAMES)[number])}
            options={[...CHART_TIMEFRAMES]}
          />
          <SelectField
            label="Period"
            value={String(periodDays)}
            onChange={(value) => setPeriodDays(Number(value) as BacktestPeriodDays)}
            options={BACKTEST_PERIOD_DAYS.map(String)}
            formatOption={(value) => `${value} days`}
          />
          <SelectField
            label="Strategy Version"
            value="v1-default-decision-engine"
            onChange={() => {}}
            options={["v1-default-decision-engine"]}
            formatOption={() => "v1 — Default Decision Engine"}
            disabled
          />
          <Button onClick={handleRun} disabled={isPending} className="gap-2">
            <PlayCircle className="size-4" />
            {isPending ? "Running..." : "Run Backtest"}
          </Button>
        </CardContent>
      </Card>

      {error ? (
        <Card className="border-danger/30 bg-danger-dim p-4 text-sm text-danger">{extractErrorDetail(error)}</Card>
      ) : null}

      {isLoadingResults ? (
        <Skeleton className="h-[420px] w-full rounded-xl" />
      ) : report && trades && equity ? (
        <>
          <BacktestSummaryCards performance={report.performance} risk={report.risk} />

          <Card>
            <CardHeader>
              <CardTitle className="text-foreground">
                Equity Curve · {report.run.symbol} {report.run.timeframe} ({report.run.periodDays}d)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <EquityCurveChart points={equity} />
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-foreground">Drawdown</CardTitle>
              </CardHeader>
              <CardContent>
                <DrawdownChart points={equity} />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-foreground">Monthly Returns</CardTitle>
              </CardHeader>
              <CardContent>
                <MonthlyReturnsChart trades={trades} />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-foreground">Trade Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <TradeDistributionChart trades={trades} />
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-foreground">Win / Loss Histogram</CardTitle>
              </CardHeader>
              <CardContent>
                <WinLossChart trades={trades} />
              </CardContent>
            </Card>
          </div>

          <TradeListTable report={report} trades={trades} />
        </>
      ) : (
        <Card className="flex h-40 items-center justify-center text-sm text-muted-foreground">
          Configure your parameters and run a backtest to see results.
        </Card>
      )}
    </div>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
  formatOption,
  disabled,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
  formatOption?: (value: string) => string;
  disabled?: boolean;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      <Select value={value} onValueChange={onChange} disabled={disabled}>
        <SelectTrigger className="w-48">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map((option) => (
            <SelectItem key={option} value={option}>
              {formatOption ? formatOption(option) : option}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
