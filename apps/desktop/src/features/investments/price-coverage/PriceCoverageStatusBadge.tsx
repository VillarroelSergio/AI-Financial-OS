import type { CoverageStatus } from "@/lib/types/price-coverage";

const CONFIG: Record<CoverageStatus, { label: string; className: string }> = {
  OK: {
    label: "Valorado en EUR",
    className: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/25",
  },
  FX_PENDING: {
    label: "Precio OK · FX pendiente",
    className: "bg-amber-500/15 text-amber-400 border border-amber-500/25",
  },
  AMBIGUOUS: {
    label: "Ticker ambiguo",
    className: "bg-blue-500/15 text-blue-400 border border-blue-500/25",
  },
  UNAVAILABLE: {
    label: "Sin cobertura",
    className: "bg-red-500/15 text-red-400 border border-red-500/25",
  },
  MANUAL: {
    label: "Manual",
    className: "bg-stone-500/15 text-stone-400 border border-stone-500/25",
  },
  ERROR: {
    label: "Error",
    className: "bg-red-700/20 text-red-300 border border-red-700/30",
  },
};

export default function PriceCoverageStatusBadge({ status }: { status: CoverageStatus }) {
  const { label, className } = CONFIG[status] ?? CONFIG.ERROR;
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${className}`}
    >
      {label}
    </span>
  );
}
