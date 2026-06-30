import type { AuditSummary } from "@/lib/types/price-coverage";

function Card({
  label,
  value,
  highlight = "text-on-dark",
  sub,
}: {
  label: string;
  value: number;
  highlight?: string;
  sub?: string;
}) {
  return (
    <div className="flex flex-col gap-1 rounded-xl bg-surface-deep border border-hairline-dark px-5 py-4 min-w-[130px]">
      <span className={`text-2xl font-bold ${highlight}`}>{value}</span>
      <span className="text-xs text-mute leading-tight">{label}</span>
      {sub && <span className="text-[10px] text-mute/60 mt-0.5">{sub}</span>}
    </div>
  );
}

export default function PriceCoverageSummaryCards({ summary }: { summary: AuditSummary }) {
  const needsReview = summary.ambiguous + summary.error;
  return (
    <div className="flex flex-wrap gap-3">
      <Card label="Total activos" value={summary.total} />
      <Card
        label="Con precio"
        value={summary.with_price}
        highlight={summary.with_price === summary.total ? "text-emerald-400" : "text-on-dark"}
      />
      <Card
        label="Valorados en EUR"
        value={summary.eur_valued}
        highlight={summary.eur_valued === summary.total ? "text-emerald-400" : "text-on-dark"}
        sub={summary.eur_valued < summary.total ? `${summary.total - summary.eur_valued} pendientes` : undefined}
      />
      {summary.fx_pending > 0 && (
        <Card
          label="FX pendiente"
          value={summary.fx_pending}
          highlight="text-amber-400"
          sub="Precio OK · sin conversión"
        />
      )}
      {needsReview > 0 && (
        <Card
          label="Revisar"
          value={needsReview}
          highlight="text-blue-400"
          sub={summary.ambiguous > 0 ? "Ticker ambiguo" : undefined}
        />
      )}
      {summary.manual > 0 && (
        <Card label="Manual" value={summary.manual} highlight="text-stone-400" />
      )}
      {summary.unavailable > 0 && (
        <Card label="Sin cobertura" value={summary.unavailable} highlight="text-red-400" />
      )}
    </div>
  );
}
