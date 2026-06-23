import { useState } from "react";
import EmptyState from "@/components/ui/EmptyState";
import Spinner from "@/components/ui/Spinner";
import TypeBadge from "@/components/ui/TypeBadge";
import { useTransactions } from "@/lib/hooks/useTransactions";
import { useAccounts } from "@/lib/hooks/useAccounts";
import { useCategories } from "@/lib/hooks/useCategories";
import { formatCurrency } from "@/lib/formatters/currency";
import type { TransactionCreate, TransactionFilters } from "@/lib/api/transactions";

const FILTER_OPTIONS = [
  { value: "", label: "Todos" },
  { value: "income", label: "Ingresos" },
  { value: "expense", label: "Gastos" },
  { value: "transfer", label: "Transferencias" },
  { value: "investment", label: "Inversiones" },
];

const EMPTY_FORM: TransactionCreate = {
  account_id: "",
  category_id: "",
  date: new Date().toISOString().slice(0, 10),
  description: "",
  amount: "",
  currency: "EUR",
  type: "expense",
};

export default function TransactionsPage() {
  const [activeType, setActiveType] = useState("");
  const filters: TransactionFilters = activeType ? { type: activeType } : {};
  const { transactions, loading, add, remove } = useTransactions(filters);
  const { accounts } = useAccounts();
  const { categories } = useCategories();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<TransactionCreate>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await add({ ...form, category_id: form.category_id || undefined });
      setShowForm(false);
      setForm(EMPTY_FORM);
    } finally {
      setSaving(false);
    }
  };

  const getCategoryName = (id: string | null) =>
    id ? (categories.find((c) => c.id === id)?.name ?? "—") : "—";
  const getAccountName = (id: string) => accounts.find((a) => a.id === id)?.name ?? id;

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="p-2xl space-y-xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-display-lg text-on-dark">Movimientos</h1>
          <p className="text-body-sm text-stone mt-xs">
            {transactions.length} movimiento{transactions.length !== 1 ? "s" : ""}
          </p>
        </div>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="px-lg py-sm bg-primary text-on-dark text-button-md rounded-sm hover:bg-primary-bright transition-colors"
        >
          Nuevo movimiento
        </button>
      </div>

      {/* Filtros de tipo */}
      <div className="flex gap-sm">
        {FILTER_OPTIONS.map(({ value, label }) => (
          <button
            key={value}
            onClick={() => setActiveType(value)}
            className={`px-md py-xs text-caption rounded-sm transition-colors ${
              activeType === value
                ? "bg-surface-elevated text-on-dark"
                : "text-stone hover:text-on-dark"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="bg-surface-card border border-hairline-dark rounded-md p-xl space-y-lg"
        >
          <h2 className="text-heading-sm text-on-dark">Nuevo movimiento</h2>
          <div className="grid grid-cols-2 gap-lg">
            <div className="space-y-xs">
              <label className="text-caption text-stone">Descripción</label>
              <input
                required
                className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={form.description}
                onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
                placeholder="Ej. Mercadona"
              />
            </div>
            <div className="space-y-xs">
              <label className="text-caption text-stone">Importe</label>
              <input
                required
                type="number"
                step="0.01"
                className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={form.amount}
                onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))}
                placeholder="Ej. -42.30"
              />
            </div>
            <div className="space-y-xs">
              <label className="text-caption text-stone">Tipo</label>
              <select
                className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={form.type}
                onChange={(e) => setForm((f) => ({ ...f, type: e.target.value }))}
              >
                <option value="expense">Gasto</option>
                <option value="income">Ingreso</option>
                <option value="transfer">Transferencia</option>
                <option value="investment">Inversión</option>
              </select>
            </div>
            <div className="space-y-xs">
              <label className="text-caption text-stone">Fecha</label>
              <input
                required
                type="date"
                className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={form.date}
                onChange={(e) => setForm((f) => ({ ...f, date: e.target.value }))}
              />
            </div>
            <div className="space-y-xs">
              <label className="text-caption text-stone">Cuenta</label>
              <select
                required
                className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={form.account_id}
                onChange={(e) => setForm((f) => ({ ...f, account_id: e.target.value }))}
              >
                <option value="">Seleccionar cuenta</option>
                {accounts.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-xs">
              <label className="text-caption text-stone">Categoría</label>
              <select
                className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={form.category_id}
                onChange={(e) => setForm((f) => ({ ...f, category_id: e.target.value }))}
              >
                <option value="">Sin categoría</option>
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex gap-sm justify-end">
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="px-lg py-sm text-stone text-body-sm hover:text-on-dark transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-lg py-sm bg-primary text-on-dark text-button-md rounded-sm hover:bg-primary-bright disabled:opacity-50 transition-colors"
            >
              {saving ? "Guardando..." : "Guardar"}
            </button>
          </div>
        </form>
      )}

      {transactions.length === 0 ? (
        <EmptyState
          title="Sin movimientos"
          description="Añade movimientos manuales o importa un CSV."
          action={
            <button
              onClick={() => setShowForm(true)}
              className="px-lg py-sm bg-primary text-on-dark text-button-md rounded-sm hover:bg-primary-bright transition-colors"
            >
              Añadir movimiento
            </button>
          }
        />
      ) : (
        <div className="bg-surface-card border border-hairline-dark rounded-md overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-hairline-dark">
                <th className="text-left px-xl py-md text-caption text-stone font-medium">Fecha</th>
                <th className="text-left px-xl py-md text-caption text-stone font-medium">
                  Descripción
                </th>
                <th className="text-left px-xl py-md text-caption text-stone font-medium">Cuenta</th>
                <th className="text-left px-xl py-md text-caption text-stone font-medium">
                  Categoría
                </th>
                <th className="text-left px-xl py-md text-caption text-stone font-medium">Tipo</th>
                <th className="text-right px-xl py-md text-caption text-stone font-medium">
                  Importe
                </th>
                <th className="px-xl py-md" />
              </tr>
            </thead>
            <tbody>
              {transactions.map((tx) => {
                const amount = parseFloat(tx.amount);
                return (
                  <tr
                    key={tx.id}
                    className="border-b border-divider-soft hover:bg-surface-elevated/30 transition-colors"
                  >
                    <td className="px-xl py-md text-body-sm text-stone">{tx.date}</td>
                    <td className="px-xl py-md text-body-sm text-on-dark">{tx.description}</td>
                    <td className="px-xl py-md text-body-sm text-stone">
                      {getAccountName(tx.account_id)}
                    </td>
                    <td className="px-xl py-md text-body-sm text-stone">
                      {getCategoryName(tx.category_id)}
                    </td>
                    <td className="px-xl py-md">
                      <TypeBadge type={tx.type} />
                    </td>
                    <td
                      className={`px-xl py-md text-right text-body-sm font-medium ${
                        amount >= 0 ? "text-accent-teal" : "text-on-dark"
                      }`}
                    >
                      {formatCurrency(tx.amount, tx.currency)}
                    </td>
                    <td className="px-xl py-md">
                      <button
                        onClick={() => remove(tx.id)}
                        className="text-stone hover:text-accent-danger text-caption transition-colors"
                      >
                        Eliminar
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
