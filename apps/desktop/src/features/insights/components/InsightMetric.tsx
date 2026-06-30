import type { InsightMetric as InsightMetricType } from "../types/insights.types";

export function InsightMetric({ metric, large = false }: { metric: InsightMetricType; large?: boolean }) {
  const valueStr = metric.unit === "%"
    ? `${metric.value.toFixed(1)}%`
    : metric.unit === "EUR"
      ? `${metric.value.toLocaleString("es-ES", { minimumFractionDigits: 0, maximumFractionDigits: 0 })} €`
      : `${metric.value} ${metric.unit}`.trim();

  return (
    <div className="rounded-lg bg-white/5 px-3 py-2">
      <p className="text-[10px] text-stone">{metric.label}</p>
      <p className={`font-semibold text-on-dark ${large ? "text-lg" : "text-sm"}`}>{valueStr}</p>
    </div>
  );
}
