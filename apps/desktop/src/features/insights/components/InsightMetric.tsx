import { formatCurrency } from "@/lib/formatters/currency";
import type { InsightMetric as InsightMetricType } from "../types/insights.types";

function esNumber(value: number, decimals: number): string {
  return value.toLocaleString("es-ES", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

export function InsightMetric({ metric, large = false }: { metric: InsightMetricType; large?: boolean }) {
  // Formato es-ES único, con la precisión que declara el backend (INS-F1).
  const decimals = metric.precision ?? (metric.unit === "%" ? 1 : 0);
  const valueStr = metric.unit === "%"
    ? `${esNumber(metric.value, decimals)} %`
    : metric.unit === "EUR"
      ? formatCurrency(metric.value)
      : `${esNumber(metric.value, decimals)} ${metric.unit}`.trim();

  return (
    <div className="rounded-lg bg-white/5 px-3 py-2">
      <p className="text-[10px] text-stone">{metric.label}</p>
      <p className={`font-semibold text-on-dark ${large ? "text-lg" : "text-sm"}`}>{valueStr}</p>
    </div>
  );
}
