import { ChartCard } from "@/components/ui/Dashboard";
import { formatCurrency, formatPercent } from "@/lib/formatters/currency";
import type { MonthlyReview } from "../types/insights.types";

interface MonthlyReviewCardProps {
  review: MonthlyReview;
  onAskAI?: () => void;
}

const STATUS_LABEL: Record<string, string> = {
  complete: "Datos completos",
  partial: "Datos parciales",
  insufficient: "Datos insuficientes",
  empty: "Sin datos",
  error: "Error",
};

export function MonthlyReviewCard({ review, onAskAI }: MonthlyReviewCardProps) {
  return (
    <ChartCard
      title="Resumen mensual"
      description={review.period}
      action={
        onAskAI ? (
          <button onClick={onAskAI} className="rounded-md bg-primary/10 px-3 py-1.5 text-xs text-primary-bright hover:bg-primary/20 transition-colors">
            Preguntar a la IA
          </button>
        ) : undefined
      }
      className="col-span-12"
    >
      <div className="space-y-4">
        <div>
          <p className="text-base font-semibold text-on-dark">{review.headline}</p>
          <p className="mt-1 text-sm text-stone">{review.summary}</p>
        </div>
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="rounded-lg bg-[var(--bg-interactive)] p-3">
            <p className="text-[10px] text-stone">Ingresos</p>
            <p className="mt-1 financial-number text-sm text-on-dark">{formatCurrency(review.income)}</p>
          </div>
          <div className="rounded-lg bg-[var(--bg-interactive)] p-3">
            <p className="text-[10px] text-stone">Gastos</p>
            <p className="mt-1 financial-number text-sm text-on-dark">{formatCurrency(review.expenses)}</p>
          </div>
          <div className="rounded-lg bg-[var(--bg-interactive)] p-3">
            <p className="text-[10px] text-stone">Ahorro</p>
            <p className={`mt-1 financial-number text-sm ${review.savings >= 0 ? "text-accent-teal" : "text-accent-danger"}`}>
              {formatCurrency(review.savings)}
            </p>
          </div>
          <div className="rounded-lg bg-[var(--bg-interactive)] p-3">
            <p className="text-[10px] text-stone">Tasa de ahorro</p>
            <p className={`mt-1 financial-number text-sm ${review.savings_rate >= 15 ? "text-accent-teal" : "text-amber-300"}`}>
              {formatPercent(review.savings_rate / 100)}
            </p>
          </div>
        </div>
        <p className="text-[11px] text-mute">{STATUS_LABEL[review.data_status] ?? review.data_status}</p>
      </div>
    </ChartCard>
  );
}
