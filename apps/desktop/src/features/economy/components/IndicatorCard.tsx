import type { MacroDataPointMI } from "@/lib/types/market-intelligence";

const STATUS_LABELS: Record<string, string> = {
  unavailable: "Sin dato",
  seed: "Demo",
  stale: "En caché",
  limited: "Parcial",
  requires_review: "Revisar",
};

// Umbral de frescura (días) según frecuencia declarada del indicador
const STALE_DAYS: Record<string, number> = {
  daily: 7,
  weekly: 21,
  monthly: 60,
  quarterly: 150,
  yearly: 430,
  annual: 430,
};

interface Props {
  indicator: MacroDataPointMI;
  size?: "default" | "large";
}

function formatValue(value: number | undefined | null, unit: string | undefined): string {
  if (value === undefined || value === null) return "—";
  const decimals = unit === "pts" || unit === "index" ? 0 : 2;
  return value.toLocaleString("es-ES", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

/** Parsea periodos "2026", "2026-06" o "2026-06-17" a Date (fin de periodo aproximado). */
function parsePeriod(period: string): Date | null {
  const m = period.match(/^(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?/);
  if (!m) return null;
  const year = Number(m[1]);
  const month = m[2] ? Number(m[2]) - 1 : 11;
  const day = m[3] ? Number(m[3]) : 28;
  const d = new Date(year, month, day);
  return Number.isNaN(d.getTime()) ? null : d;
}

function isStale(period: string | undefined, frequency: string | undefined): boolean {
  if (!period) return false;
  const date = parsePeriod(period);
  if (!date) return false;
  const limit = STALE_DAYS[frequency ?? "monthly"] ?? 60;
  return (Date.now() - date.getTime()) / 86_400_000 > limit;
}

function Sparkline({ values }: { values: number[] }) {
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const w = 100;
  const h = 24;
  const points = values
    .map((v, i) => {
      const x = (i / (values.length - 1)) * w;
      const y = h - 2 - ((v - min) / range) * (h - 4);
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-6 text-stone/70" preserveAspectRatio="none" aria-hidden>
      <polyline points={points} fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
}

export default function IndicatorCard({ indicator, size = "default" }: Props) {
  const isUnavailable = indicator.value === undefined || indicator.value === null;
  const unitSuffix = indicator.unit && indicator.unit !== "index" ? ` ${indicator.unit}` : "";
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
  const history = indicator.history ?? [];
  const delta = indicator.delta;
  const hasDelta = delta !== undefined && delta !== null && !isUnavailable;
  const stale = isStale(indicator.period, indicator.frequency);

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
          className={`text-stone truncate ${size === "large" ? "text-base" : "text-sm"}`}
        >
          {title}
        </span>
        <span
          className={`text-xs ${qualityColor} flex-shrink-0`}
          title={`Calidad: ${(indicator.quality_score * 100).toFixed(0)}%`}
        >
          ●
        </span>
      </div>

      <div
        className={`font-semibold tabular-nums flex items-center gap-2 flex-wrap ${
          size === "large" ? "text-3xl" : "text-2xl"
        } ${isUnavailable ? "text-stone" : "text-on-dark"}`}
      >
        {valueStr}
        {hasDelta && (
          <span
            className={`inline-flex items-center gap-0.5 rounded px-1.5 py-0.5 text-sm font-semibold tabular-nums ${
              delta > 0
                ? "bg-emerald-500/15 text-emerald-400"
                : delta < 0
                ? "bg-rose-500/15 text-rose-400"
                : "bg-white/10 text-stone"
            }`}
            title={`Variación vs periodo anterior (${formatValue(indicator.previous_value, indicator.unit)})`}
          >
            {delta > 0 ? "▲" : delta < 0 ? "▼" : "＝"}
            {Math.abs(delta).toLocaleString("es-ES", { maximumFractionDigits: 2 })}
          </span>
        )}
        {indicator.data_status && indicator.data_status !== "ok" && (
          <span className="rounded px-1.5 py-0.5 text-xs font-medium uppercase tracking-wide bg-white/10 text-stone">
            {STATUS_LABELS[indicator.data_status] ?? indicator.data_status}
          </span>
        )}
      </div>

      {history.length >= 3 && <Sparkline values={history.map((p) => p.value)} />}

      {indicator.period && (
        <div className="text-xs text-mute mt-auto pt-1 border-t border-hairline-dark flex items-center gap-2">
          <span>{indicator.period}</span>
          {stale && (
            <span className="rounded px-1 py-px text-[10px] font-medium uppercase tracking-wide bg-amber-400/10 text-amber-400">
              Antiguo
            </span>
          )}
        </div>
      )}
    </div>
  );
}
