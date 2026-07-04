import { useCallback, useEffect, useState } from "react";
import { Check, Link2, RefreshCw, X } from "lucide-react";
import { EmptyState, PageHeader } from "@/components/ui/Dashboard";
import Spinner from "@/components/ui/Spinner";
import { useCategories } from "@/lib/hooks/useCategories";
import { formatCurrency } from "@/lib/formatters/currency";
import {
  fetchReconciliation,
  resolveScope,
  runReconciliation,
  type ReconciliationItem,
  type ReconciliationStats,
} from "@/lib/api/transactions";

export default function ReconciliationPage() {
  const [items, setItems] = useState<ReconciliationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [stats, setStats] = useState<ReconciliationStats | null>(null);
  const { categories } = useCategories();

  const categoryName = (id: string | null) =>
    id ? (categories.find((c) => c.id === id)?.name ?? "Sin categoría") : "Sin categoría";

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setItems(await fetchReconciliation());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar la conciliación");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleRun = async () => {
    setRunning(true);
    try {
      setStats(await runReconciliation());
      await load();
    } finally {
      setRunning(false);
    }
  };

  const resolve = async (
    id: string,
    scope: "personal" | "excluded",
    linkedId?: string
  ) => {
    await resolveScope(id, scope, linkedId);
    setItems((prev) => prev.filter((item) => item.transaction.id !== id));
  };

  return (
    <div className="space-y-6 p-8">
      <PageHeader
        title="Conciliación"
        description="Movimientos bancarios pendientes de cruzar con tus gastos personales (Monefy)"
        actions={
          <button
            onClick={handleRun}
            disabled={running}
            className="flex items-center gap-2 rounded-lg bg-[var(--primary)] px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            <RefreshCw size={16} className={running ? "animate-spin" : ""} />
            Conciliar automáticamente
          </button>
        }
      />
      {stats && (
        <p className="text-sm text-[var(--text-secondary)]">
          Última ejecución: {stats.auto_linked} enlazados automáticamente,{" "}
          {stats.categories_propagated} categorías propagadas, {stats.suggestions} sugerencias
          pendientes.
        </p>
      )}
      {error && <p className="text-sm text-red-400">{error}</p>}
      {loading ? (
        <Spinner />
      ) : items.length === 0 ? (
        <EmptyState
          title="Todo conciliado"
          description="No hay movimientos bancarios pendientes de revisión."
        />
      ) : (
        <div className="space-y-3">
          {items.map(({ transaction: tx, account_name, suggestion }) => (
            <div
              key={tx.id}
              className="rounded-xl border p-4"
              style={{ borderColor: "var(--border-soft)", background: "var(--bg-card)" }}
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2 text-sm font-medium text-[var(--text-primary)]">
                    <span>{tx.description}</span>
                    <span className="text-xs text-[var(--text-secondary)]">
                      {tx.date} · {account_name ?? tx.source_name ?? "Banco"} ·{" "}
                      {categoryName(tx.category_id)}
                    </span>
                  </div>
                  <div
                    className={`text-base font-semibold ${
                      Number(tx.amount) < 0 ? "text-red-400" : "text-emerald-400"
                    }`}
                  >
                    {formatCurrency(tx.amount, tx.currency)}
                  </div>
                  {suggestion && (
                    <div className="mt-1 flex items-center gap-2 text-xs text-[var(--text-secondary)]">
                      <Link2 size={12} />
                      <span>
                        Candidato Monefy: {suggestion.description || "(sin descripción)"} ·{" "}
                        {suggestion.date} · {formatCurrency(suggestion.amount)} ·{" "}
                        {categoryName(suggestion.category_id)} · confianza{" "}
                        {(suggestion.score * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}
                </div>
                <div className="flex gap-2">
                  {suggestion && (
                    <button
                      onClick={() => resolve(tx.id, "excluded", suggestion.id)}
                      className="flex items-center gap-1 rounded-lg border px-3 py-1.5 text-xs text-[var(--text-primary)]"
                      style={{ borderColor: "var(--border-soft)" }}
                      title="Enlazar con el gasto Monefy: el banco deja de contar en analítica"
                    >
                      <Link2 size={14} /> Vincular
                    </button>
                  )}
                  <button
                    onClick={() => resolve(tx.id, "personal")}
                    className="flex items-center gap-1 rounded-lg border px-3 py-1.5 text-xs text-[var(--text-primary)]"
                    style={{ borderColor: "var(--border-soft)" }}
                    title="Contar como gasto personal (no está en Monefy)"
                  >
                    <Check size={14} /> Es personal
                  </button>
                  <button
                    onClick={() => resolve(tx.id, "excluded")}
                    className="flex items-center gap-1 rounded-lg border px-3 py-1.5 text-xs text-[var(--text-secondary)]"
                    style={{ borderColor: "var(--border-soft)" }}
                    title="Excluir de la analítica (compartido o no personal)"
                  >
                    <X size={14} /> Excluir
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
