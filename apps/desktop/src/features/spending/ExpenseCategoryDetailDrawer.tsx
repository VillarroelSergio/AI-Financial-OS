import { ArrowDown, ArrowUp, Search, X } from "lucide-react";
import { useMemo, useState } from "react";
import { useCategorySpendingDetail } from "@/lib/hooks/useDashboard";
import { formatCurrency } from "@/lib/formatters/currency";
import type { CategorySpending } from "@/lib/api/dashboard";

type SortMode = "date_desc" | "date_asc" | "amount_desc" | "amount_asc";

interface Props {
  category: CategorySpending | null;
  period: { mode: "month" | "year"; month: string; year: number };
  onClose: () => void;
}

export default function ExpenseCategoryDetailDrawer({ category, period, onClose }: Props) {
  const [query, setQuery] = useState("");
  const [sortMode, setSortMode] = useState<SortMode>("date_desc");
  const { data, loading, error } = useCategorySpendingDetail(category?.category_id, period);

  const transactions = useMemo(() => {
    const filtered = (data?.transactions ?? []).filter((tx) =>
      tx.description.toLowerCase().includes(query.trim().toLowerCase()),
    );
    return [...filtered].sort((a, b) => {
      if (sortMode === "date_desc") return b.date.localeCompare(a.date);
      if (sortMode === "date_asc") return a.date.localeCompare(b.date);
      const amountA = Math.abs(Number(a.amount));
      const amountB = Math.abs(Number(b.amount));
      return sortMode === "amount_desc" ? amountB - amountA : amountA - amountB;
    });
  }, [data?.transactions, query, sortMode]);

  if (!category) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/60">
      <aside className="ml-auto flex h-full w-full max-w-2xl flex-col border-l border-hairline-dark bg-canvas-dark shadow-2xl">
        <div className="border-b border-hairline-dark p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-caption uppercase tracking-widest text-primary">Detalle de categoria</p>
              <h2 className="mt-2 text-heading-md text-on-dark">{data?.category ?? category.category}</h2>
              <p className="mt-1 text-body-sm text-stone">{period.mode === "year" ? period.year : period.month}</p>
            </div>
            <button onClick={onClose} aria-label="Cerrar" className="rounded-lg p-2 text-stone hover:bg-white/5 hover:text-on-dark">
              <X size={18} />
            </button>
          </div>
          <div className="mt-5 grid grid-cols-2 gap-3 md:grid-cols-4">
            <div className="rounded-lg bg-surface-elevated p-3">
              <p className="text-caption text-stone">Total</p>
              <p className="financial-number mt-1 text-body-md font-semibold">{formatCurrency(data?.total ?? category.amount)}</p>
            </div>
            <div className="rounded-lg bg-surface-elevated p-3">
              <p className="text-caption text-stone">Peso</p>
              <p className="financial-number mt-1 text-body-md font-semibold">{(data?.percentage ?? category.percentage).toFixed(1)}%</p>
            </div>
            <div className="rounded-lg bg-surface-elevated p-3">
              <p className="text-caption text-stone">Movimientos</p>
              <p className="financial-number mt-1 text-body-md font-semibold">{data?.transaction_count ?? 0}</p>
            </div>
            <div className="rounded-lg bg-surface-elevated p-3">
              <p className="text-caption text-stone">Media</p>
              <p className="financial-number mt-1 text-body-md font-semibold">{formatCurrency(data?.average_transaction ?? "0")}</p>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-3 border-b border-hairline-dark p-4">
          <label className="flex min-w-0 flex-1 items-center gap-2 rounded-lg border border-hairline-dark bg-surface-elevated px-3 py-2">
            <Search size={15} className="shrink-0 text-stone" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Buscar descripcion"
              className="min-w-0 flex-1 bg-transparent text-body-sm text-on-dark outline-none placeholder:text-stone"
            />
          </label>
          <select
            value={sortMode}
            onChange={(e) => setSortMode(e.target.value as SortMode)}
            className="rounded-lg border border-hairline-dark bg-surface-elevated px-3 py-2 text-body-sm text-on-dark outline-none"
          >
            <option value="date_desc">Fecha descendente</option>
            <option value="date_asc">Fecha ascendente</option>
            <option value="amount_desc">Importe mayor</option>
            <option value="amount_asc">Importe menor</option>
          </select>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          {loading && <p className="py-8 text-center text-body-sm text-stone">Cargando movimientos...</p>}
          {error && !loading && <p className="py-8 text-center text-body-sm text-accent-danger">No se pudieron cargar los movimientos de esta categoria.</p>}
          {!loading && !error && transactions.length === 0 && (
            <p className="py-8 text-center text-body-sm text-stone">No hay movimientos para esta categoria en el periodo seleccionado.</p>
          )}
          {!loading && !error && transactions.length > 0 && (
            <div className="divide-y divide-divider-soft rounded-lg border border-hairline-dark bg-surface-elevated">
              {transactions.map((tx) => {
                const isExpense = Number(tx.amount) < 0;
                return (
                  <div key={tx.id} className="grid grid-cols-[1fr_auto] gap-4 px-4 py-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        {isExpense ? <ArrowDown size={14} className="text-accent-danger" /> : <ArrowUp size={14} className="text-accent-teal" />}
                        <p className="truncate text-body-sm font-medium text-on-dark">{tx.description}</p>
                      </div>
                      <p className="mt-1 text-caption text-stone">{tx.date} · {tx.account_name} · {tx.category}</p>
                      {tx.notes && <p className="mt-1 text-caption text-mute">{tx.notes}</p>}
                    </div>
                    <div className="text-right">
                      <p className={`financial-number text-body-sm font-semibold ${isExpense ? "text-accent-danger" : "text-accent-teal"}`}>
                        {formatCurrency(tx.amount)}
                      </p>
                      <p className="mt-1 text-caption text-stone">{tx.type === "expense" ? "Gasto" : "Ingreso"}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}
