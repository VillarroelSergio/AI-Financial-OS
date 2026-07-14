import { useState } from "react";
import type { FormEvent } from "react";
import { Pencil, Trash2 } from "lucide-react";
import { EmptyState, PageHeader } from "@/components/ui/Dashboard";
import MetricCard from "@/components/ui/MetricCard";
import Spinner from "@/components/ui/Spinner";
import { useAccounts } from "@/lib/hooks/useAccounts";
import { formatCurrency } from "@/lib/formatters/currency";
import type { Account } from "@/lib/types";
import type { AccountCreate } from "@/lib/api/accounts";

const ACCOUNT_TYPE_LABELS: Record<string, string> = {
  cash: "Efectivo",
  bank: "Banco",
  broker: "Broker",
  savings: "Ahorros",
  investment: "Inversion",
  mortgage: "Deuda",
  other: "Otro",
};

const EMPTY_FORM: AccountCreate = {
  name: "",
  type: "bank",
  currency: "EUR",
  current_balance: "0.00",
  is_liability: false,
};

export default function AccountsPage() {
  const { accounts, loading, add, update, remove } = useAccounts();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<AccountCreate>(EMPTY_FORM);
  const [editing, setEditing] = useState<Account | null>(null);
  const [saving, setSaving] = useState(false);

  const total = accounts.reduce((sum, account) => sum + Number(account.current_balance), 0);
  const liquidity = accounts.filter((account) => ["cash", "bank", "savings"].includes(account.type)).reduce((sum, account) => sum + Number(account.current_balance), 0);
  const savings = accounts.filter((account) => account.type === "savings").reduce((sum, account) => sum + Number(account.current_balance), 0);
  const lastUpdated = accounts.reduce<string | null>((latest, account) => !latest || account.updated_at > latest ? account.updated_at : latest, null);

  const resetForm = () => {
    setForm(EMPTY_FORM);
    setEditing(null);
    setShowForm(false);
  };

  const openNew = () => {
    setForm(EMPTY_FORM);
    setEditing(null);
    setShowForm(true);
  };

  const openEdit = (account: Account) => {
    setEditing(account);
    setForm({
      name: account.name,
      type: account.type,
      institution: account.institution ?? "",
      currency: account.currency,
      current_balance: account.current_balance,
      is_liability: account.is_liability,
    });
    setShowForm(true);
  };

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setSaving(true);
    try {
      if (editing) {
        await update(editing.id, form);
      } else {
        await add(form);
      }
      resetForm();
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
    <div className="page-shell space-y-xl">
      <PageHeader
        eyebrow="Liquidez local"
        title="Cuentas"
        description="Resumen operativo de liquidez, ahorro y brokers con pesos sobre patrimonio."
        actions={
        <button onClick={openNew} className="ui-pressable mercury-button-primary px-lg py-sm text-button-md rounded-lg">
          Nueva cuenta
        </button>
        }
      />

      <div className="grid grid-cols-5 gap-lg">
        <MetricCard label="Saldo total" value={formatCurrency(total)} />
        <MetricCard label="Numero de cuentas" value={String(accounts.length)} />
        <MetricCard label="Liquidez inmediata" value={formatCurrency(liquidity)} />
        <MetricCard label="Cuentas de ahorro" value={formatCurrency(savings)} />
        <MetricCard label="Ultima actualizacion" value={lastUpdated ? new Date(lastUpdated).toLocaleDateString("es-ES") : "Sin datos"} />
      </div>

      {showForm && (
        <form onSubmit={handleSubmit} className="premium-card rounded-lg p-xl space-y-lg">
          <h2 className="text-heading-sm text-on-dark">{editing ? "Editar cuenta" : "Nueva cuenta"}</h2>
          <div className="grid grid-cols-2 gap-lg">
            <label className="space-y-xs">
              <span className="text-caption text-stone">Nombre</span>
              <input required className="w-full bg-[var(--bg-interactive)] border border-hairline-dark rounded-lg px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary" value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} placeholder="Ej. BBVA" />
            </label>
            <label className="space-y-xs">
              <span className="text-caption text-stone">Tipo</span>
              <select className="w-full bg-[var(--bg-interactive)] border border-hairline-dark rounded-lg px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary" value={form.type} onChange={(e) => setForm((f) => ({ ...f, type: e.target.value }))}>
                {Object.entries(ACCOUNT_TYPE_LABELS).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
              </select>
            </label>
            <label className="space-y-xs">
              <span className="text-caption text-stone">Saldo</span>
              <input type="number" step="0.01" className="w-full bg-[var(--bg-interactive)] border border-hairline-dark rounded-lg px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary" value={form.current_balance} onChange={(e) => setForm((f) => ({ ...f, current_balance: e.target.value }))} />
            </label>
            <label className="space-y-xs">
              <span className="text-caption text-stone">Divisa</span>
              <input maxLength={3} className="w-full bg-[var(--bg-interactive)] border border-hairline-dark rounded-lg px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary" value={form.currency ?? "EUR"} onChange={(e) => setForm((f) => ({ ...f, currency: e.target.value.toUpperCase() }))} />
            </label>
            <label className="space-y-xs col-span-2">
              <span className="text-caption text-stone">Institucion</span>
              <input className="w-full bg-[var(--bg-interactive)] border border-hairline-dark rounded-lg px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary" value={form.institution ?? ""} onChange={(e) => setForm((f) => ({ ...f, institution: e.target.value }))} placeholder="Opcional" />
            </label>
            <label className="flex items-center gap-sm col-span-2 cursor-pointer">
              <input type="checkbox" checked={form.is_liability ?? false} onChange={(e) => setForm((f) => ({ ...f, is_liability: e.target.checked }))} />
              <span className="text-caption text-stone">Es un pasivo (hipoteca, préstamo, deuda) — resta del patrimonio neto</span>
            </label>
          </div>
          <div className="flex gap-sm justify-end">
            <button type="button" onClick={resetForm} className="ui-pressable mercury-button px-lg py-sm rounded-lg text-body-sm">Cancelar</button>
            <button type="submit" disabled={saving} className="ui-pressable mercury-button-primary px-lg py-sm text-button-md rounded-lg disabled:opacity-50">
              {saving ? "Guardando..." : editing ? "Actualizar" : "Guardar"}
            </button>
          </div>
        </form>
      )}

      {accounts.length === 0 ? (
        <EmptyState title="Sin cuentas" description="Anade tu primera cuenta para empezar a registrar movimientos." action={<button onClick={openNew} className="ui-pressable mercury-button-primary px-lg py-sm text-button-md rounded-lg">Anadir cuenta</button>} />
      ) : (
        <div className="space-y-sm">
          {accounts.map((account) => {
            const share = liquidity > 0 && ["cash", "bank", "savings"].includes(account.type) ? (Number(account.current_balance) / liquidity) * 100 : 0;
            return (
              <div key={account.id} className="premium-card rounded-lg p-xl grid grid-cols-[1fr_auto] gap-lg">
                <div>
                  <p className="text-body-md text-on-dark">
                    {account.name}
                    {account.is_liability && <span className="ml-sm rounded-full bg-accent-danger/10 px-2 py-0.5 text-caption text-accent-danger align-middle">Pasivo</span>}
                  </p>
                  <p className="text-caption text-stone mt-xs">{ACCOUNT_TYPE_LABELS[account.type] ?? account.type}{account.institution ? ` · ${account.institution}` : ""}</p>
                  <p className="text-caption text-stone mt-xs">{share.toFixed(1)}% sobre liquidez total · {account.is_liability ? "Resta del patrimonio neto" : "Incluida en patrimonio neto"}</p>
                </div>
                <div className="flex items-center gap-xl">
                  <div className="text-right">
                    <p className="text-heading-sm text-on-dark">{formatCurrency(account.current_balance, account.currency)}</p>
                    <p className="text-caption text-stone">{account.currency}</p>
                  </div>
                  <button onClick={() => openEdit(account)} className="ui-pressable text-stone hover:text-on-dark" aria-label="Editar cuenta"><Pencil size={16} /></button>
                  <button onClick={() => remove(account.id)} className="ui-pressable text-stone hover:text-accent-danger" aria-label="Eliminar cuenta"><Trash2 size={16} /></button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
