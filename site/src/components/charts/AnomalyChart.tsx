import { useEffect, useRef } from "react";
import * as Plot from "@observablehq/plot";

export interface AnomalyChartProps {
  data: { period: string; value: number | null }[];
  anomalyPeriod: string;
  unit: string;
  title: string;
  locale: "it" | "en";
}

function periodToDate(p: string): Date {
  if (p.includes("-Q")) {
    const [y, q] = p.split("-Q");
    return new Date(Number(y), (Number(q) - 1) * 3, 1);
  }
  if (p.includes("-")) {
    const [y, m] = p.split("-");
    return new Date(Number(y), Number(m) - 1, 1);
  }
  return new Date(Number(p), 0, 1);
}

export default function AnomalyChart({
  data,
  anomalyPeriod,
  unit,
  title,
  locale,
}: AnomalyChartProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;

    const rows = data
      .filter((d) => d.value !== null)
      .map((d) => ({ date: periodToDate(d.period), value: d.value as number, period: d.period }));

    const anomalyRow = rows.find((r) => r.period === anomalyPeriod);

    const width = el.clientWidth || 640;

    const plot = Plot.plot({
      width,
      height: 260,
      marginLeft: 48,
      marginBottom: 28,
      marginTop: 10,
      style: {
        background: "transparent",
        fontFamily: "-apple-system, BlinkMacSystemFont, Inter, system-ui, sans-serif",
        fontSize: "11px",
      },
      x: { type: "time", label: null, tickFormat: locale === "it" ? "%b %y" : "%b %y" },
      y: { label: unit, grid: true, nice: true },
      marks: [
        Plot.ruleY([0], { stroke: "transparent" }),
        Plot.line(rows, {
          x: "date",
          y: "value",
          stroke: "currentColor",
          strokeOpacity: 0.7,
          strokeWidth: 1.4,
        }),
        Plot.dot(rows, {
          x: "date",
          y: "value",
          r: 1.8,
          fill: "currentColor",
          fillOpacity: 0.4,
        }),
        ...(anomalyRow
          ? [
              Plot.dot([anomalyRow], {
                x: "date",
                y: "value",
                r: 6,
                fill: "var(--accent)",
                stroke: "var(--bg)",
                strokeWidth: 2,
              }),
              Plot.text([anomalyRow], {
                x: "date",
                y: "value",
                text: (d: { value: number }) => d.value.toFixed(2),
                dy: -14,
                fill: "var(--accent)",
                fontWeight: 600,
              }),
            ]
          : []),
      ],
    });

    el.innerHTML = "";
    el.appendChild(plot);
    return () => {
      plot.remove();
    };
  }, [data, anomalyPeriod, unit, locale]);

  return (
    <div>
      <div ref={ref} role="img" aria-label={title} />
    </div>
  );
}
