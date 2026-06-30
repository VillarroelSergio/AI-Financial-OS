import type { InsightSeverity } from "../types/insights.types";

const CONFIG: Record<InsightSeverity, { label: string; className: string }> = {
  positive: { label: "Positivo", className: "bg-accent-teal/10 text-accent-teal" },
  info: { label: "Información", className: "bg-sky-400/10 text-sky-300" },
  warning: { label: "Atención", className: "bg-amber-400/10 text-amber-300" },
  critical: { label: "Crítico", className: "bg-accent-danger/10 text-accent-danger" },
};

export function InsightSeverityBadge({ severity }: { severity: InsightSeverity }) {
  const { label, className } = CONFIG[severity];
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-[11px] font-medium ${className}`}>
      {label}
    </span>
  );
}
