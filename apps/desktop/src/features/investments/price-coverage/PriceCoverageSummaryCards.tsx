import type { AuditSummary } from "@/lib/types/price-coverage";

function Card({
  label,
  value,
  highlight = "text-on-dark",
}: {
  label: string;
  value: number;
  highlight?: string;
}) {
  return (
    <div className="flex flex-col gap-1 rounded-xl bg-surface-deep border border-hairline-dark px-5 py-4 min-w-[110px]">
      <span className={`text-2xl font-bold ${highlight}`}>{value}</span>
      <span className="text-xs text-mute">{label}</span>
    </div>
  );
}

export default function PriceCoverageSummaryCards({ summary }: { summary: AuditSummary }) {
  const needsReview = summary.partial + summary.ambiguous + summary.error;
  return (
    <div className="flex flex-wrap gap-3">
      <Card label="Total activos" value={summary.total} />
      <Card label="OK" value={summary.ok} highlight="text-emerald-400" />
      <Card
        label="Revisar"
        value={needsReview}
        highlight={needsReview > 0 ? "text-amber-400" : "text-on-dark"}
      />
      <Card label="Manual" value={summary.manual} highlight="text-stone-400" />
      <Card
        label="Sin cobertura"
        value={summary.unavailable}
        highlight={summary.unavailable > 0 ? "text-red-400" : "text-on-dark"}
      />
    </div>
  );
}
