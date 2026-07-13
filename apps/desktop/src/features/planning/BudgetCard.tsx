import type { BudgetComparisonItem } from "@/lib/api/budgets";

interface Props {
  item: BudgetComparisonItem;
}

export default function BudgetCard({ item }: Props) {
  const pct = Math.min(item.consumption_pct, 100);
  const barColor = item.over_budget
    ? "bg-accent-danger"
    : item.alert
    ? "bg-accent-warning"
    : "bg-accent-teal";

  return (
    <div className="rounded-xl bg-surface-elevated p-4 space-y-3">
      <div className="flex items-start justify-between">
        <p className="text-sm font-medium text-on-dark">{item.category_name}</p>
        <span className={[
          "text-xs font-semibold",
          item.over_budget ? "text-accent-danger" : item.alert ? "text-accent-warning" : "text-stone",
        ].join(" ")}>
          {item.consumption_pct.toFixed(0)}%
        </span>
      </div>

      <div className="h-1.5 w-full rounded-full bg-[var(--bg-interactive)] overflow-hidden">
        <div
          className={`h-full rounded-full transition-all ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>

      <div className="flex justify-between text-xs text-stone">
        <span>
          {item.actual_amount.toLocaleString("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 })}
          {" gastado"}
        </span>
        <span>
          {"de "}
          {item.budget_amount.toLocaleString("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 })}
        </span>
      </div>

      {item.over_budget && (
        <p className="text-[11px] text-accent-danger">
          +{Math.abs(item.remaining).toLocaleString("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 })} sobre el límite
        </p>
      )}
    </div>
  );
}
