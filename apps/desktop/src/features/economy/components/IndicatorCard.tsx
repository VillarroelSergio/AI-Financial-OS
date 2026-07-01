import type { MacroDataPointMI } from "@/lib/types/market-intelligence";

const STATUS_LABELS: Record<string, string> = {
  unavailable: "Sin dato",
  seed: "Demo",
  stale: "En caché",
  limited: "Parcial",
  requires_review: "Revisar",
};

interface Props {
  indicator: MacroDataPointMI;
  size?: "default" | "large";
}

function formatValue(value: number | undefined, unit: string | undefined): string {
  if (value === undefined || value === null) return "—";
  const decimals = unit === "pts" || unit === "index" ? 0 : 2;
  return value.toLocaleString("es-ES", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export default function IndicatorCard({ indicator, size = "default" }: Props) {
  const isUnavailable = indicator.value === undefined || indicator.value === null;
  const unitSuffix = indicator.unit ? ` ${indicator.unit}` : "";
  const valueStr = isUnavailable
    ? "—"
    : `${formatValue(indicator.value, indicator.unit)}${unitSuffix}`;

  const qualityColor =
    indicator.quality_score >= 0.8
      ? "text-accent-success"
      : indicator.quality_score >= 0.5
      ? "text-amber-400"
      : "text-accent-danger";

  const title = indicator.display_name ?? indicator.catalog_item_id.replace(/_/g, " ");

  return (
    <div
      className={[
        "rounded-xl border border-hairline-dark bg-surface-elevated p-4 flex flex-col gap-2",
        size === "large" ? "p-5" : "",
      ].join(" ")}
      title={indicator.description ?? undefined}
    >
      <div className="flex items-center justify-between gap-2">
        <span
          className={`text-stone truncate ${size === "large" ? "text-body-sm" : "text-caption"}`}
        >
          {title}
        </span>
        <span
          className={`text-[10px] ${qualityColor} flex-shrink-0`}
          title={`Calidad: ${(indicator.quality_score * 100).toFixed(0)}%`}
        >
          ●
        </span>
      </div>

      <div
        className={`font-semibold tabular-nums flex items-center gap-2 ${
          size === "large" ? "text-2xl" : "text-xl"
        } ${isUnavailable ? "text-stone" : "text-on-dark"}`}
      >
        {valueStr}
        {indicator.data_status && indicator.data_status !== "ok" && (
          <span className="rounded px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide bg-white/10 text-stone">
            {STATUS_LABELS[indicator.data_status] ?? indicator.data_status}
          </span>
        )}
      </div>

      {indicator.period && (
        <div className="text-[10px] text-mute mt-auto pt-1 border-t border-hairline-dark">
          {indicator.period}
        </div>
      )}
    </div>
  );
}
