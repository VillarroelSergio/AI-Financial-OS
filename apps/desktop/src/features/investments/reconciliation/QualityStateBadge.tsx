import type { ReconciliationHolding } from "@/lib/api/investments";

type QualityState = ReconciliationHolding["quality_state"];

const CONFIG: Record<QualityState, { label: string; classes: string }> = {
  confirmed:       { label: "Confirmado",   classes: "bg-accent-teal/15 text-accent-teal" },
  estimated:       { label: "Estimado",     classes: "bg-accent-warning/15 text-accent-warning" },
  manual:          { label: "Manual",       classes: "bg-[var(--bg-interactive)] text-stone" },
  no_price:        { label: "Sin precio",   classes: "bg-accent-yellow/15 text-accent-yellow" },
  fx_pending:      { label: "FX pendiente", classes: "bg-sky-500/15 text-sky-400" },
  requires_review: { label: "Revisar",      classes: "bg-accent-danger/15 text-accent-danger" },
};

export default function QualityStateBadge({ state }: { state: QualityState }) {
  const { label, classes } = CONFIG[state] ?? CONFIG.requires_review;
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-medium ${classes}`}>
      {label}
    </span>
  );
}
