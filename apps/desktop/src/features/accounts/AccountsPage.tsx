import { useState } from "react";
import EmptyState from "@/components/ui/EmptyState";
import Spinner from "@/components/ui/Spinner";
import { useAccounts } from "@/lib/hooks/useAccounts";
import { formatCurrency } from "@/lib/formatters/currency";
import type { AccountCreate } from "@/lib/api/accounts";

const ACCOUNT_TYPE_LABELS: Record<string, string> = {
  cash: "Efectivo",
  bank: "Banco",
  broker: "Broker",
  savings: "Ahorros",
  investment: "Inversión",
  mortgage: "Hipoteca",
  other: "Otro",
};

const EMPTY_FORM: AccountCreate = {
  name: "",
  type: "bank",
  currency: "EUR",
  current_balance: "0.00",
};

export default function AccountsPage() {
  const { accounts, loading, add, remove } = useAccounts();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<AccountCreate>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    try {
      await add(form);
      setShowForm(false);
      setForm(EMPTY_FORM);
    } finally {
      setSaving(false);
    }
  };

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
          <h1 className="text-display-lg text-on-dark">Cuentas</h1>
          <p className="text-body-sm text-stone mt-xs">
            {accounts.length} cuenta{accounts.length !== 1 ? "s" : ""}
          </p>
        </div>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="px-lg py-sm bg-primary text-on-dark text-button-md rounded-sm hover:bg-primary-bright transition-colors"
        >
          Nueva cuenta
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleSubmit}
          className="bg-surface-card border border-hairline-dark rounded-md p-xl space-y-lg"
        >
          <h2 className="text-heading-sm text-on-dark">Nueva cuenta</h2>
          <div className="grid grid-cols-2 gap-lg">
            <div className="space-y-xs">
              <label className="text-caption text-stone">Nombre</label>
              <input
                required
                className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={form.name}
                onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                placeholder="Ej. BBVA"
              />
            </div>
            <div className="space-y-xs">
              <label className="text-caption text-stone">Tipo</label>
              <select
                className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={form.type}
                onChange={(e) => setForm((f) => ({ ...f, type: e.target.value }))}
              >
                {Object.entries(ACCOUNT_TYPE_LABELS).map(([v, l]) => (
                  <option key={v} value={v}>
                    {l}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-xs">
              <label className="text-caption text-stone">Saldo inicial</label>
              <input
                type="number"
                step="0.01"
                className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={form.current_balance}
                onChange={(e) => setForm((f) => ({ ...f, current_balance: e.target.value }))}
              />
            </div>
            <div className="space-y-xs">
              <label className="text-caption text-stone">Institución</label>
              <input
                className="w-full bg-surface-elevated border border-hairline-dark rounded-sm px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={form.institution ?? ""}
                onChange={(e) => setForm((f) => ({ ...f, institution: e.target.value }))}
                placeholder="Opcional"
              />
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

      {accounts.length === 0 ? (
        <EmptyState
          title="Sin cuentas"
          description="Añade tu primera cuenta para empezar a registrar movimientos."
          action={
            <button
              onClick={() => setShowForm(true)}
              className="px-lg py-sm bg-primary text-on-dark text-button-md rounded-sm hover:bg-primary-bright transition-colors"
            >
              Añadir cuenta
            </button>
          }
        />
      ) : (
        <div className="space-y-sm">
          {accounts.map((account) => (
            <div
              key={account.id}
              className="bg-surface-card border border-hairline-dark rounded-md p-xl flex items-center justify-between"
            >
              <div>
                <p className="text-body-md text-on-dark">{account.name}</p>
                <p className="text-caption text-stone mt-xs">
                  {ACCOUNT_TYPE_LABELS[account.type] ?? account.type}
                  {account.institution ? ` · ${account.institution}` : ""}
                </p>
              </div>
              <div className="flex items-center gap-xl">
                <p className="text-heading-sm text-on-dark">
                  {formatCurrency(account.current_balance, account.currency)}
                </p>
                <button
                  onClick={() => remove(account.id)}
                  className="text-stone hover:text-accent-danger text-caption transition-colors"
                >
                  Eliminar
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
