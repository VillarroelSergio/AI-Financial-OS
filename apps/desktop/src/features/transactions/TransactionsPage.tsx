import { useMemo, useState } from "react";
import { Edit3, Plus, Search, SlidersHorizontal, Trash2 } from "lucide-react";
import { PageHeader } from "@/components/ui/Dashboard";
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
  const [query, setQuery] = useState("");
  const [accountFilter, setAccountFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [minAmount, setMinAmount] = useState("");
  const [maxAmount, setMaxAmount] = useState("");
  const [sortBy, setSortBy] = useState<"date_desc" | "date_asc" | "amount_desc" | "amount_asc" | "category_asc">("date_desc");
  const filters: TransactionFilters = {
    ...(activeType ? { type: activeType } : {}),
    ...(accountFilter ? { account_id: accountFilter } : {}),
    ...(categoryFilter ? { category_id: categoryFilter } : {}),
    ...(fromDate ? { from_date: fromDate } : {}),
    ...(toDate ? { to_date: toDate } : {}),
  };
  const { transactions, loading, error, add, update, remove } = useTransactions(filters);
  const { accounts } = useAccounts();
  const { categories } = useCategories();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<TransactionCreate>(EMPTY_FORM);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const accountName = (id: string) => accounts.find((a) => a.id === id)?.name ?? "Cuenta sin nombre";
  const categoryName = (id: string | null) => id ? (categories.find((c) => c.id === id)?.name ?? "Sin categoria") : "Sin categoria";

  const visibleTransactions = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return transactions.filter((tx) => {
      const amount = Math.abs(Number(tx.amount));
      if (minAmount && amount < Number(minAmount)) return false;
      if (maxAmount && amount > Number(maxAmount)) return false;
      if (!normalized) return true;
      return [
        tx.description,
        tx.date,
        tx.amount,
        tx.currency,
        accountName(tx.account_id),
        categoryName(tx.category_id),
      ].some((value) => value.toLowerCase().includes(normalized));
    }).sort((a, b) => {
      if (sortBy === "date_asc") return a.date.localeCompare(b.date);
      if (sortBy === "amount_desc") return Number(b.amount) - Number(a.amount);
      if (sortBy === "amount_asc") return Number(a.amount) - Number(b.amount);
      if (sortBy === "category_asc") return categoryName(a.category_id).localeCompare(categoryName(b.category_id));
      return b.date.localeCompare(a.date);
    });
  }, [transactions, minAmount, maxAmount, query, accounts, categories, sortBy]);

  const total = visibleTransactions.reduce((sum, tx) => sum + Number(tx.amount), 0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setStatusMessage(null);
    try {
      const payload = { ...form, category_id: form.category_id || undefined };
      if (editingId) {
        await update(editingId, payload);
        setStatusMessage("Movimiento actualizado.");
      } else {
        await add(payload);
        setStatusMessage("Movimiento creado.");
      }
      setShowForm(false);
      setEditingId(null);
      setForm(EMPTY_FORM);
    } finally {
      setSaving(false);
    }
  };

  const startEdit = (id: string) => {
    const tx = transactions.find((item) => item.id === id);
    if (!tx) return;
    setEditingId(id);
    setForm({
      account_id: tx.account_id,
      category_id: tx.category_id ?? "",
      date: tx.date,
      description: tx.description,
      amount: tx.amount,
      currency: tx.currency,
      type: tx.type,
      notes: tx.notes ?? undefined,
    });
    setShowForm(true);
  };

  const handleDelete = async (id: string, description: string) => {
    if (!window.confirm(`Eliminar el movimiento "${description}"? Esta accion no se puede deshacer.`)) return;
    setStatusMessage(null);
    await remove(id);
    setStatusMessage("Movimiento eliminado.");
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner />
      </div>
    );
  }

  return (
    <div className="p-8 max-w-[1500px] mx-auto space-y-6">
      <PageHeader
        eyebrow="Ledger financiero"
        title="Movimientos"
        description={`${transactions.length} movimientos registrados. Busca, filtra y audita sin exponer identificadores internos.`}
        actions={
          <button onClick={() => setShowForm((v) => !v)} className="mercury-button-primary inline-flex items-center gap-2 rounded-lg px-4 py-2.5 text-sm font-semibold">
            <Plus size={16} />
            Nuevo movimiento
          </button>
        }
      />

      <section className="premium-card rounded-lg p-4">
        <div className="grid gap-3 lg:grid-cols-[1fr_180px_220px_220px_auto]">
          <label className="flex items-center gap-2 rounded-lg border border-hairline-dark bg-white/[.035] px-3 py-2">
            <Search size={16} className="text-mute" />
            <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Buscar descripcion, cuenta, categoria..." className="w-full bg-transparent text-sm text-on-dark placeholder:text-mute" />
          </label>
          <select value={activeType} onChange={(e) => setActiveType(e.target.value)} className="rounded-lg border border-hairline-dark bg-white/[.035] px-3 py-2 text-sm text-on-dark">
            {FILTER_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
          </select>
          <select value={accountFilter} onChange={(e) => setAccountFilter(e.target.value)} className="rounded-lg border border-hairline-dark bg-white/[.035] px-3 py-2 text-sm text-on-dark">
            <option value="">Todas las cuentas</option>
            {accounts.map((account) => <option key={account.id} value={account.id}>{account.name}</option>)}
          </select>
          <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)} className="rounded-lg border border-hairline-dark bg-white/[.035] px-3 py-2 text-sm text-on-dark">
            <option value="">Todas las categorias</option>
            {categories.map((category) => <option key={category.id} value={category.id}>{category.name}</option>)}
          </select>
          <div className="flex items-center gap-2 rounded-lg border border-hairline-dark bg-white/[.035] px-3 py-2 text-sm text-stone">
            <SlidersHorizontal size={16} />
            <span className="financial-number">{visibleTransactions.length}</span>
          </div>
        </div>
        <div className="mt-3 grid gap-3 lg:grid-cols-[160px_160px_160px_160px_220px]">
          <label className="space-y-1"><span className="text-[11px] text-stone">Desde</span><input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} className="w-full rounded-lg border border-hairline-dark bg-white/[.035] px-3 py-2 text-sm text-on-dark" /></label>
          <label className="space-y-1"><span className="text-[11px] text-stone">Hasta</span><input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} className="w-full rounded-lg border border-hairline-dark bg-white/[.035] px-3 py-2 text-sm text-on-dark" /></label>
          <label className="space-y-1"><span className="text-[11px] text-stone">Importe min.</span><input type="number" step="0.01" value={minAmount} onChange={(e) => setMinAmount(e.target.value)} className="w-full rounded-lg border border-hairline-dark bg-white/[.035] px-3 py-2 text-sm text-on-dark" /></label>
          <label className="space-y-1"><span className="text-[11px] text-stone">Importe max.</span><input type="number" step="0.01" value={maxAmount} onChange={(e) => setMaxAmount(e.target.value)} className="w-full rounded-lg border border-hairline-dark bg-white/[.035] px-3 py-2 text-sm text-on-dark" /></label>
          <label className="space-y-1"><span className="text-[11px] text-stone">Orden</span><select value={sortBy} onChange={(e) => setSortBy(e.target.value as typeof sortBy)} className="w-full rounded-lg border border-hairline-dark bg-white/[.035] px-3 py-2 text-sm text-on-dark"><option value="date_desc">Fecha reciente</option><option value="date_asc">Fecha antigua</option><option value="amount_desc">Importe mayor</option><option value="amount_asc">Importe menor</option><option value="category_asc">Categoria A-Z</option></select></label>
        </div>
      </section>

      {error && <div className="rounded-lg border border-accent-danger/30 bg-accent-danger/5 p-4 text-sm text-accent-danger">No se han podido cargar los movimientos. Revisa el backend local.</div>}
      {statusMessage && <div className="rounded-lg border border-accent-teal/30 bg-accent-teal/10 p-4 text-sm text-accent-teal">{statusMessage}</div>}

      {showForm && (
        <form onSubmit={handleSubmit} className="premium-card rounded-lg p-xl space-y-lg">
          <h2 className="text-heading-sm text-on-dark">{editingId ? "Editar movimiento" : "Nuevo movimiento"}</h2>
          <div className="grid grid-cols-2 gap-lg">
            <label className="space-y-xs"><span className="text-caption text-stone">Descripcion</span><input required className="w-full bg-white/[.035] border border-hairline-dark rounded-lg px-md py-sm text-body-sm text-on-dark" value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} placeholder="Ej. Mercadona" /></label>
            <label className="space-y-xs"><span className="text-caption text-stone">Importe</span><input required type="number" step="0.01" className="w-full bg-white/[.035] border border-hairline-dark rounded-lg px-md py-sm text-body-sm text-on-dark" value={form.amount} onChange={(e) => setForm((f) => ({ ...f, amount: e.target.value }))} placeholder="Ej. -42.30" /></label>
            <label className="space-y-xs"><span className="text-caption text-stone">Tipo</span><select className="w-full bg-white/[.035] border border-hairline-dark rounded-lg px-md py-sm text-body-sm text-on-dark" value={form.type} onChange={(e) => setForm((f) => ({ ...f, type: e.target.value }))}><option value="expense">Gasto</option><option value="income">Ingreso</option><option value="transfer">Transferencia</option><option value="investment">Inversion</option></select></label>
            <label className="space-y-xs"><span className="text-caption text-stone">Fecha</span><input required type="date" className="w-full bg-white/[.035] border border-hairline-dark rounded-lg px-md py-sm text-body-sm text-on-dark" value={form.date} onChange={(e) => setForm((f) => ({ ...f, date: e.target.value }))} /></label>
            <label className="space-y-xs"><span className="text-caption text-stone">Cuenta</span><select required={!editingId} className="w-full bg-white/[.035] border border-hairline-dark rounded-lg px-md py-sm text-body-sm text-on-dark" value={form.account_id} onChange={(e) => setForm((f) => ({ ...f, account_id: e.target.value }))}><option value="">Sin cuenta asignada</option>{accounts.map((a) => <option key={a.id} value={a.id}>{a.name}</option>)}</select></label>
            <label className="space-y-xs"><span className="text-caption text-stone">Categoria</span><select className="w-full bg-white/[.035] border border-hairline-dark rounded-lg px-md py-sm text-body-sm text-on-dark" value={form.category_id} onChange={(e) => setForm((f) => ({ ...f, category_id: e.target.value }))}><option value="">Sin categoria</option>{categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
          </div>
          <div className="flex gap-sm justify-end">
            <button type="button" onClick={() => { setShowForm(false); setEditingId(null); setForm(EMPTY_FORM); }} className="mercury-button rounded-lg px-lg py-sm text-body-sm">Cancelar</button>
            <button type="submit" disabled={saving} className="mercury-button-primary rounded-lg px-lg py-sm text-button-md disabled:opacity-50">{saving ? "Guardando..." : editingId ? "Actualizar" : "Guardar"}</button>
          </div>
        </form>
      )}

      {visibleTransactions.length === 0 ? (
        <EmptyState title="Sin movimientos para esta vista" description="Ajusta los filtros, importa un CSV o anade un movimiento manual." action={<button onClick={() => setShowForm(true)} className="mercury-button-primary rounded-lg px-lg py-sm text-button-md">Anadir movimiento</button>} />
      ) : (
        <div className="premium-card rounded-lg overflow-hidden">
          <div className="flex items-center justify-between border-b border-hairline-dark px-5 py-3">
            <p className="text-sm font-semibold text-on-dark">Ledger</p>
            <p className={`financial-number text-sm ${total >= 0 ? "text-accent-teal" : "text-accent-danger"}`}>{formatCurrency(total)}</p>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-black/20">
                <tr className="border-b border-hairline-dark">
                  {["Fecha", "Descripcion", "Cuenta", "Categoria", "Tipo", "Importe", ""].map((header) => (
                    <th key={header} className="text-left px-xl py-md text-caption text-stone font-medium">{header}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {visibleTransactions.map((tx) => {
                  const amount = parseFloat(tx.amount);
                  return (
                    <tr key={tx.id} className="border-b border-divider-soft hover:bg-white/[.025] transition-colors">
                      <td className="px-xl py-md text-body-sm text-stone whitespace-nowrap">{tx.date}</td>
                      <td className="px-xl py-md text-body-sm text-on-dark min-w-[220px]">{tx.description}</td>
                      <td className="px-xl py-md text-body-sm text-stone">{accountName(tx.account_id)}</td>
                      <td className="px-xl py-md text-body-sm text-stone">{categoryName(tx.category_id)}</td>
                      <td className="px-xl py-md"><TypeBadge type={tx.type} /></td>
                      <td className={`financial-number px-xl py-md text-right text-body-sm font-medium ${amount >= 0 ? "text-accent-teal" : "text-on-dark"}`}>{formatCurrency(tx.amount, tx.currency)}</td>
                      <td className="px-xl py-md text-right">
                        <div className="flex justify-end gap-2">
                          <button aria-label={`Editar ${tx.description}`} onClick={() => startEdit(tx.id)} className="text-stone hover:text-primary-bright transition-colors"><Edit3 size={15} /></button>
                          <button aria-label={`Eliminar ${tx.description}`} onClick={() => handleDelete(tx.id, tx.description)} className="text-stone hover:text-accent-danger transition-colors"><Trash2 size={15} /></button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
