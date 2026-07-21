"use client";

interface BarChartDatum {
  label: string;
  value: number;
}

interface BarChartProps {
  data: BarChartDatum[];
  height?: number;
  formatValue?: (value: number) => string;
  positiveColor?: string;
  negativeColor?: string;
}

/**
 * A plain CSS bar chart for categorical/distribution data (monthly
 * returns, trade PnL buckets, win/loss counts) — lightweight-charts
 * (the project's TradingView-based library, see components/charts/line-chart.tsx)
 * is a financial time-series renderer that requires a strictly
 * increasing time axis, which doesn't fit these categorical shapes.
 */
export function BarChart({
  data,
  height = 220,
  formatValue = (value) => value.toFixed(2),
  positiveColor = "#00e676",
  negativeColor = "#f6465d",
}: BarChartProps) {
  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center text-sm text-muted-foreground" style={{ height }}>
        No data yet.
      </div>
    );
  }

  const maxAbs = Math.max(1e-9, ...data.map((d) => Math.abs(d.value)));

  return (
    <div className="flex items-end gap-1.5 overflow-x-auto" style={{ height }}>
      {data.map((d) => {
        const barHeightPercent = (Math.abs(d.value) / maxAbs) * 100;
        const color = d.value >= 0 ? positiveColor : negativeColor;
        return (
          <div key={d.label} className="flex min-w-[28px] flex-1 flex-col items-center justify-end gap-1.5 self-stretch">
            <div className="flex flex-1 w-full items-end justify-center">
              <div
                title={`${d.label}: ${formatValue(d.value)}`}
                className="w-full rounded-t-sm transition-opacity hover:opacity-80"
                style={{ height: `${Math.max(2, barHeightPercent)}%`, backgroundColor: color }}
              />
            </div>
            <span className="max-w-full truncate text-[10px] text-muted-foreground" title={d.label}>
              {d.label}
            </span>
          </div>
        );
      })}
    </div>
  );
}
