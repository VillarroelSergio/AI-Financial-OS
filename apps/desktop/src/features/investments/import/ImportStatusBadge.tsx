import type { ImportStatus } from "@/lib/types/portfolio-import";

interface Config {
  label: string;
  className: string;
}

const STATUS_MAP: Record<ImportStatus, Config> = {
  READY: {
    label: "Listo",
    className: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/25",
  },
  REQUIRES_CONFIRMATION: {
    label: "Requiere confirmación",
    className: "bg-blue-500/15 text-blue-400 border border-blue-500/25",
  },
  NO_PRICE: {
    label: "Sin precio",
    className: "bg-amber-500/15 text-amber-400 border border-amber-500/25",
  },
  MANUAL: {
    label: "Manual",
    className: "bg-stone-500/15 text-stone-400 border border-stone-500/25",
  },
  REVIEW: {
    label: "Revisar",
    className: "bg-amber-500/15 text-amber-400 border border-amber-500/25",
  },
  DISCARDED: {
    label: "Descartado",
    className: "bg-stone-500/10 text-stone-600 border border-stone-500/15",
  },
  IMPORTED: {
    label: "Importado",
    className: "bg-emerald-500/15 text-emerald-400 border border-emerald-500/25",
  },
  ERROR: {
    label: "Error",
    className: "bg-red-500/15 text-red-400 border border-red-500/25",
  },
};

export default function ImportStatusBadge({ status }: { status: ImportStatus }) {
  const { label, className } = STATUS_MAP[status] ?? STATUS_MAP.REVIEW;
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[11px] font-medium whitespace-nowrap ${className}`}>
      {label}
    </span>
  );
}
