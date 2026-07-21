"use client";

import { LineChart } from "@/components/charts/line-chart";
import type { EquityPoint } from "@/types";

export function EquityCurveChart({ points }: { points: EquityPoint[] }) {
  const data = points.map((p) => ({ time: p.time, value: p.balance }));
  return <LineChart data={data} height={320} color="#00e676" />;
}
