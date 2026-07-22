"use client";

import { LineChart } from "@/components/charts/line-chart";
import type { EquityPoint } from "@/types";

/** "Underwater" curve: 0 at each new equity peak, dipping negative
 * during a drawdown — the standard way to visualize drawdown over time. */
export function DrawdownChart({ points }: { points: EquityPoint[] }) {
  const data = points.map((p) => ({ time: p.time, value: -p.drawdownPercent }));
  return <LineChart data={data} height={220} color="#f6465d" />;
}
