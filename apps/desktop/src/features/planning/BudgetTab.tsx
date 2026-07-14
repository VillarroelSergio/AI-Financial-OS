import { useState } from "react";
import { Plus, RefreshCw } from "lucide-react";
import BudgetCard from "./BudgetCard";
import BudgetFormModal from "./BudgetFormModal";
import type { BudgetCreate } from "@/lib/api/budgets";
import { useBudgetComparison, useBudgets } from "@/lib/hooks/useBudgets";

export default function BudgetTab() {
  const { add } = useBudgets();
  const { data, loading, error, refresh: refreshComparison } = useBudgetComparison();
  const [showModal, setShowModal] = useState(false);

  const handleAddBudget = async (body: BudgetCreate) => {
    await add(body);
    await refreshComparison();
  };

  const overBudget = data.filter(i => i.over_budget).length;
  const totalBudget = data.reduce((s, i) => s + i.budget_amount, 0);
  const totalSpent = data.reduce((s, i) => s + i.actual_amount, 0);

  if (loading) {
    return (
      <div className="premium-card flex h-48 items-center justify-center rounded-xl">
        <div className="flex items-center gap-2 text-sm text-stone">
          <RefreshCw size={18} className="animate-spin text-stone" />
          <span>Preparando la planificaciÃ³n...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="premium-card flex h-48 flex-col items-center justify-center gap-3 rounded-xl px-6 text-center">
        <p className="text-sm font-medium text-on-dark">No se ha podido cargar la comparativa de presupuestos</p>
        <p className="text-xs text-stone">Vuelve a intentarlo; tus datos no se han modificado.</p>
        <button onClick={refreshComparison} className="mercury-button rounded-lg px-4 py-2 text-sm text-on-dark">Reintentar</button>
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
        <BudgetFormModal onSubmit={handleAddBudget} onClose={() => setShowModal(false)} />
      )}
    </div>
  );
}
