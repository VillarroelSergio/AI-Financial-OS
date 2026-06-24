// apps/desktop/src/features/markets/components/LiveIndicator.tsx
import type { FreshnessStatus } from "@/lib/types";

interface Props {
  secondsSinceUpdate: number;
  /** Worst freshness across all visible quotes. Defaults to "unknown". */
  freshnessStatus?: FreshnessStatus;
}

const FRESHNESS_CONFIG: Record<
  FreshnessStatus,
  { label: string; dotClass: string; textClass: string }
> = {
  live:    { label: "En vivo",              dotClass: "bg-accent-teal live-dot",    textClass: "text-accent-teal" },
  fresh:   { label: "Actualizado",          dotClass: "bg-accent-teal live-dot",    textClass: "text-accent-teal" },
  delayed: { label: "Dato retrasado",       dotClass: "bg-accent-warning",          textClass: "text-accent-warning" },
  eod:     { label: "Último cierre",        dotClass: "bg-stone",                   textClass: "text-stone" },
  closed:  { label: "Mercado cerrado",      dotClass: "bg-stone",                   textClass: "text-stone" },
  stale:   { label: "Datos desactualizados",dotClass: "bg-accent-warning",          textClass: "text-accent-warning" },
  error:   { label: "Error de datos",       dotClass: "bg-accent-danger",           textClass: "text-accent-danger" },
  unknown: { label: "No verificado",        dotClass: "bg-stone",                   textClass: "text-stone" },
};

export default function LiveIndicator({
  secondsSinceUpdate,
  freshnessStatus = "unknown",
}: Props) {
  const cfg = FRESHNESS_CONFIG[freshnessStatus] ?? FRESHNESS_CONFIG.unknown;

  return (
    <div
      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-hairline-dark bg-surface-elevated"
      role="status"
      aria-label={`${cfg.label}. Actualizado hace ${secondsSinceUpdate} segundos`}
    >
      <span
        className={`inline-block w-2 h-2 rounded-full flex-shrink-0 ${cfg.dotClass}`}
        aria-hidden="true"
      />
      <span className={`text-caption font-medium ${cfg.textClass}`}>{cfg.label}</span>
      <span className="text-caption text-stone">·</span>
      <span className="text-caption text-stone tabular-nums">
        Actualizado hace {secondsSinceUpdate}s
      </span>
    </div>
  );
}
