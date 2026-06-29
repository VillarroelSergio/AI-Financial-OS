import { useState } from "react";
import { Plus, RefreshCw } from "lucide-react";
import RecurringItem from "./RecurringItem";
import RecurringFormModal from "./RecurringFormModal";
import UpcomingCalendar from "./UpcomingCalendar";
import { useCalendar, useRecurring } from "@/lib/hooks/useBudgets";

export default function RecurringTab() {
  const { recurring, loading, error, add, remove } = useRecurring();
  const { events } = useCalendar(30);
  const [showModal, setShowModal] = useState(false);

  const expenses = recurring.filter(r => r.type === "expense" && r.active);
  const incomes = recurring.filter(r => r.type === "income" && r.active);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <RefreshCw size={20} className="animate-spin text-stone" />
        <span className="ml-2 text-sm text-stone">Cargando recurrentes...</span>
      </div>
    );
  }

  if (error) {
    return <p className="py-12 text-center text-sm text-accent-danger">{error}</p>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-on-dark">Transacciones recurrentes</h2>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-xs font-medium text-white hover:bg-primary/90 transition-colors"
        >
          <Plus size={14} />
          Añadir
        </button>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-3">
          <p className="text-sm font-medium text-on-dark">Gastos fijos ({expenses.length})</p>
          {expenses.length === 0
            ? <p className="text-sm text-stone">Sin gastos recurrentes.</p>
            : expenses.map(r => <RecurringItem key={r.id} item={r} onDelete={remove} />)
          }
        </div>
        <div className="space-y-3">
          <p className="text-sm font-medium text-on-dark">Ingresos fijos ({incomes.length})</p>
          {incomes.length === 0
            ? <p className="text-sm text-stone">Sin ingresos recurrentes.</p>
            : incomes.map(r => <RecurringItem key={r.id} item={r} onDelete={remove} />)
          }
        </div>
      </div>

      <div className="rounded-xl bg-surface-elevated p-5">
        <p className="mb-3 text-sm font-medium text-on-dark">Próximos 30 días</p>
        <UpcomingCalendar events={events} />
      </div>

      {showModal && <RecurringFormModal onSubmit={add} onClose={() => setShowModal(false)} />}
    </div>
  );
}
