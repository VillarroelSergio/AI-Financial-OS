import { useState } from "react";
import { Plus, RefreshCw } from "lucide-react";
import RecurringItem from "./RecurringItem";
import RecurringFormModal from "./RecurringFormModal";
import UpcomingCalendar from "./UpcomingCalendar";
import { useCalendar, useRecurring } from "@/lib/hooks/useBudgets";
import { formatCurrency } from "@/lib/formatters/currency";
import type { RecurringCandidate } from "@/lib/api/budgets";

export default function RecurringTab() {
  const { recurring, candidates, loading, error, add, remove } = useRecurring();
  const { events } = useCalendar(30);
  const [showModal, setShowModal] = useState(false);
  const [ignored, setIgnored] = useState<string[]>([]);

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

  const visibleCandidates = candidates.filter((candidate) => !ignored.includes(candidate.id));
  const confirmCandidate = (candidate: RecurringCandidate) => add({
    name: candidate.name,
    category_id: candidate.category_id,
    account_id: candidate.account_id,
    amount: candidate.amount,
    currency: candidate.currency,
    type: candidate.type,
    frequency: candidate.frequency,
    day_of_month: candidate.frequency === "monthly" ? Number(candidate.next_date.slice(8, 10)) : null,
    next_date: candidate.next_date,
    description: `Creado desde candidato asistido. Evidencia: ${candidate.evidence.join(" | ")}`,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-on-dark">Transacciones recurrentes</h2>
          <p className="mt-1 text-sm text-stone">La deteccion es asistida: nada se convierte en recurrente sin confirmacion.</p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-1.5 rounded-lg bg-primary px-3 py-2 text-xs font-medium text-white hover:bg-primary/90 transition-colors"
        >
          <Plus size={14} />
          Añadir
        </button>
      </div>

      {visibleCandidates.length > 0 && (
        <section className="rounded-lg border border-primary/20 bg-primary/5 p-4">
          <div className="mb-3 flex items-center justify-between">
            <div>
              <p className="text-sm font-semibold text-on-dark">Candidatos detectados</p>
              <p className="text-xs text-stone">Patrones encontrados en movimientos similares. Revisa importe, frecuencia y evidencias antes de confirmar.</p>
            </div>
            <span className="rounded-lg border border-hairline-dark bg-[var(--bg-interactive)] px-2.5 py-1 text-xs text-primary-bright">{visibleCandidates.length} pendientes</span>
          </div>
          <div className="grid gap-3">
            {visibleCandidates.map((candidate) => (
              <article key={candidate.id} className="rounded-lg border border-hairline-dark bg-surface-card p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="text-sm font-semibold text-on-dark">{candidate.name}</p>
                    <p className="mt-1 text-xs text-stone">{candidate.description}</p>
                  </div>
                  <div className="text-right">
                    <p className="financial-number text-sm text-on-dark">{formatCurrency(candidate.amount, candidate.currency)}</p>
                    <p className="text-xs text-stone">{candidate.frequency} · confianza {(candidate.confidence * 100).toFixed(0)}%</p>
                  </div>
                </div>
                <div className="mt-3 grid gap-2 md:grid-cols-3">
                  <div className="rounded-lg bg-[var(--bg-interactive)] px-3 py-2"><span className="text-[11px] text-stone">Proxima fecha</span><p className="text-xs text-on-dark">{candidate.next_date}</p></div>
                  <div className="rounded-lg bg-[var(--bg-interactive)] px-3 py-2"><span className="text-[11px] text-stone">Rango habitual</span><p className="text-xs text-on-dark">{formatCurrency(candidate.amount_min, candidate.currency)} - {formatCurrency(candidate.amount_max, candidate.currency)}</p></div>
                  <div className="rounded-lg bg-[var(--bg-interactive)] px-3 py-2"><span className="text-[11px] text-stone">Movimientos usados</span><p className="text-xs text-on-dark">{candidate.transaction_count}</p></div>
                </div>
                <details className="mt-3">
                  <summary className="cursor-pointer text-xs text-primary-bright">Ver evidencia</summary>
                  <ul className="mt-2 space-y-1 text-xs text-stone">
                    {candidate.evidence.map((item) => <li key={item}>{item}</li>)}
                  </ul>
                </details>
                <div className="mt-4 flex justify-end gap-2">
                  <button onClick={() => setIgnored((prev) => [...prev, candidate.id])} className="rounded-lg border border-hairline-dark px-3 py-2 text-xs text-stone hover:text-on-dark">Ignorar</button>
                  <button onClick={() => confirmCandidate(candidate)} className="rounded-lg bg-primary px-3 py-2 text-xs font-medium text-white hover:bg-primary/90">Confirmar recurrente</button>
                </div>
              </article>
            ))}
          </div>
        </section>
      )}

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
