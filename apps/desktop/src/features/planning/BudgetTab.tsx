import { useState } from "react";
import { Plus, RefreshCw } from "lucide-react";
import BudgetCard from "./BudgetCard";
import BudgetFormModal from "./BudgetFormModal";
import { useBudgetComparison, useBudgets } from "@/lib/hooks/useBudgets";

export default function BudgetTab() {
  const { add, refresh } = useBudgets();
  const { data, loading, error } = useBudgetComparison();
  const [showModal, setShowModal] = useState(false);

  const overBudget = data.filter(i => i.over_budget).length;
  const totalBudget = data.reduce((s, i) => s + i.budget_amount, 0);
  const totalSpent = data.reduce((s, i) => s + i.actual_amount, 0);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <RefreshCw size={20} className="animate-spin text-stone" />
        <span className="ml-2 text-sm text-stone">Cargando presupuestos...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3">
        <p className="text-sm text-accent-danger">{error}</p>
        <button onClick={refresh} className="rounded-lg bg-white/5 px-4 py-2 text-sm text-on-dark hover:bg-white/8">Reintentar</button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-on-dark">Presupuestos</h2>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-xs font-medium text-white hover:bg-primary/90 transition-colors"
        >
          <Plus size={14} />
          Nuevo presupuesto
        </button>
      </div>

      {data.length === 0 ? (
        <div className="flex h-48 flex-col items-center justify-center gap-3 rounded-xl bg-surface-elevated">
          <p className="text-sm text-stone">Crea tu primer presupuesto para controlar tus gastos</p>
          <button onClick={() => setShowModal(true)} className="rounded-lg bg-primary px-4 py-2 text-sm text-white">
            Crear presupuesto
          </button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-3">
            {[
              { label: "Total presupuestado", value: totalBudget.toLocaleString("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }) },
              { label: "Total gastado", value: totalSpent.toLocaleString("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }) },
              { label: "Sobre límite", value: String(overBudget) },
            ].map(kpi => (
              <div key={kpi.label} className="rounded-xl bg-surface-elevated p-4">
                <p className="text-[11px] uppercase tracking-wide text-stone">{kpi.label}</p>
                <p className="mt-1.5 text-xl font-semibold text-on-dark">{kpi.value}</p>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {data.map(item => <BudgetCard key={item.budget_id} item={item} />)}
          </div>
        </>
      )}

      {showModal && (
        <BudgetFormModal onSubmit={add} onClose={() => setShowModal(false)} />
      )}
    </div>
  );
}
