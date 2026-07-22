interface RadarAxis {
  label: string;
  value: number | null; // 0-100; null renders as a 0-value axis with a muted label
}

interface RadarChartProps {
  axes: RadarAxis[];
  size?: number;
  className?: string;
}

const RING_FRACTIONS = [0.33, 0.66, 1.0];

function pointOnAxis(index: number, count: number, radius: number, center: number): [number, number] {
  const angle = (Math.PI * 2 * index) / count - Math.PI / 2;
  return [center + radius * Math.cos(angle), center + radius * Math.sin(angle)];
}

export function RadarChart({ axes, size = 260, className }: RadarChartProps) {
  const center = size / 2;
  const maxRadius = size / 2 - 36;
  const count = axes.length;

  const dataPoints = axes
    .map((axis, i) => pointOnAxis(i, count, (Math.max(0, axis.value ?? 0) / 100) * maxRadius, center))
    .map(([x, y]) => `${x},${y}`)
    .join(" ");

  return (
    <svg width={size} height={size} className={className} role="img" aria-label="Sentiment radar chart">
      {RING_FRACTIONS.map((fraction) => {
        const points = Array.from({ length: count }, (_, i) => pointOnAxis(i, count, maxRadius * fraction, center))
          .map(([x, y]) => `${x},${y}`)
          .join(" ");
        return (
          <polygon key={fraction} points={points} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={1} />
        );
      })}

      {axes.map((axis, i) => {
        const [x, y] = pointOnAxis(i, count, maxRadius, center);
        return (
          <line key={axis.label} x1={center} y1={center} x2={x} y2={y} stroke="rgba(255,255,255,0.08)" strokeWidth={1} />
        );
      })}

      <polygon points={dataPoints} fill="rgba(0,230,118,0.18)" stroke="#00e676" strokeWidth={1.5} />

      {axes.map((axis, i) => {
        const [x, y] = pointOnAxis(i, count, maxRadius + 20, center);
        return (
          <text
            key={axis.label}
            x={x}
            y={y}
            textAnchor="middle"
            dominantBaseline="middle"
            className={axis.value === null ? "fill-muted-foreground" : "fill-foreground"}
            fontSize={11}
          >
            {axis.label}
            {axis.value === null ? " (N/A)" : ""}
          </text>
        );
      })}
    </svg>
  );
}
