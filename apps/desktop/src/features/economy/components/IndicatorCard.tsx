import type { EconomicIndicator } from "@/lib/types";

interface Props {
  indicator: EconomicIndicator;
  size?: "default" | "large";
}

function formatValue(value: number | null, unit: string): string {
  if (value === null) return "—";
  const decimals = unit === "pts" || unit === "BUSD" || unit === "M€" ? 0 : 2;
  return value.toLocaleString("es-ES", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function formatChange(change: number | null, unit: string): string {
  if (change === null) return "";
  const prefix = change > 0 ? "▲ +" : change < 0 ? "▼ " : "";
  const decimals = unit === "pts" ? 0 : 2;
  return `${prefix}${change.toLocaleString("es-ES", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })} ${unit === "pts" ? "pts" : unit === "USD" ? "" : "pp"}`;
}

const INDICATOR_UNIT_SUFFIX: Record<string, string> = {
  "%": "%",
  "pts": " pts",
  "USD": "",
  "BUSD": " B$",
  "M€": " M€",
};

export default function IndicatorCard({ indicator, size = "default" }: Props) {
  const positive = (indicator.change ?? 0) >= 0;
  const hasChange = indicator.change !== null;
  const isUnavailable = indicator.value === null;

  const unitSuffix = INDICATOR_UNIT_SUFFIX[indicator.unit] ?? indicator.unit;
  const valueStr = isUnavailable
    ? "—"
    : `${formatValue(indicator.value, indicator.unit)}${unitSuffix}`;

  return (
    <div
      className={[
        "rounded-xl border border-hairline-dark bg-surface-elevated p-4 flex flex-col gap-2",
        size === "large" ? "p-5" : "",
      ].join(" ")}
    >
      <div className="flex items-center justify-between gap-2">
        <span className={`text-stone truncate ${size === "large" ? "text-body-sm" : "text-caption"}`}>
          {indicator.name}
        </span>
        {indicator.is_stale && (
          <span className="text-[10px] text-amber-400 bg-amber-400/10 rounded px-1.5 py-0.5 flex-shrink-0">
            DESACTUALIZADO
          </span>
        )}
      </div>

      <div className={`font-semibold tabular-nums ${size === "large" ? "text-2xl" : "text-xl"} ${isUnavailable ? "text-stone" : "text-on-dark"}`}>
        {valueStr}
      </div>

      {hasChange && (
        <div className={`text-caption tabular-nums ${positive ? "text-accent-success" : "text-accent-danger"}`}>
          {formatChange(indicator.change, indicator.unit)}
          {indicator.period && (
            <span className="text-mute ml-1">vs {indicator.period}</span>
          )}
        </div>
      )}

      {isUnavailable && (
        <p className="text-[10px] text-stone leading-tight">
          Configura <code className="text-primary">FRED_API_KEY</code> para ver este dato
        </p>
      )}

      <div className="text-[10px] text-mute mt-auto pt-1 border-t border-hairline-dark">
        {indicator.source} · {indicator.period}
      </div>
    </div>
  );
}
