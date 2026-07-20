"use client";

import { useState } from "react";
import { PlayCircle } from "lucide-react";

import { BACKTEST_STRATEGIES } from "@/lib/mock/backtest";
import { WATCHLIST_SYMBOLS } from "@/lib/constants";
import { formatPercent } from "@/lib/utils";
import { useRunBacktest } from "@/hooks/use-backtest";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { StatTile } from "@/components/common/stat-tile";
import { LineChart } from "@/components/charts/line-chart";

const TIMEFRAMES = ["15m", "1H", "4H", "1D"];

export function BacktestRunner() {
  const [strategy, setStrategy] = useState(BACKTEST_STRATEGIES[0]);
  const [symbol, setSymbol] = useState(WATCHLIST_SYMBOLS[0]);
  const [timeframe, setTimeframe] = useState(TIMEFRAMES[1]);

  const { mutate, data: result, isPending } = useRunBacktest();

  function handleRun() {
    mutate({ strategy, symbol, timeframe });
  }

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="text-foreground">Configure Backtest</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap items-end gap-4">
          <SelectField label="Strategy" value={strategy} onChange={setStrategy} options={BACKTEST_STRATEGIES} />
          <SelectField label="Symbol" value={symbol} onChange={setSymbol} options={WATCHLIST_SYMBOLS} />
          <SelectField label="Timeframe" value={timeframe} onChange={setTimeframe} options={TIMEFRAMES} />
          <Button onClick={handleRun} disabled={isPending} className="gap-2">
            <PlayCircle className="size-4" />
            {isPending ? "Running..." : "Run Backtest"}
          </Button>
        </CardContent>
      </Card>

      {isPending ? (
        <Skeleton className="h-[420px] w-full rounded-xl" />
      ) : result ? (
        <>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
            <StatTile label="Total Trades" value={String(result.totalTrades)} />
            <StatTile label="Win Rate" value={`${result.winRate.toFixed(1)}%`} tone="positive" />
            <StatTile label="Profit Factor" value={result.profitFactor.toFixed(2)} />
            <StatTile
              label="Total Return"
              value={formatPercent(result.totalReturnPercent)}
              tone={result.totalReturnPercent >= 0 ? "positive" : "negative"}
            />
            <StatTile label="Max Drawdown" value={formatPercent(result.maxDrawdownPercent)} tone="negative" />
            <StatTile label="Sharpe Ratio" value={result.sharpeRatio.toFixed(2)} />
          </div>

          <Card>
            <CardHeader>
              <CardTitle className="text-foreground">
                Equity Curve · {result.strategy} on {result.symbol} ({result.period})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <LineChart data={result.equityCurve} height={320} />
            </CardContent>
          </Card>
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
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="w-44">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map((option) => (
            <SelectItem key={option} value={option}>
              {option}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
