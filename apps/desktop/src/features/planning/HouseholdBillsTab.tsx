import { useState } from "react";
import { Home, Plus, Trash2 } from "lucide-react";
import { formatCurrency } from "@/lib/formatters/currency";
import { useHouseholdBills } from "@/lib/hooks/useHouseholdBills";
import type { HouseholdBillCreate } from "@/lib/api/household-bills";

const SERVICE_OPTIONS = [
  ["electricity", "Luz"],
  ["gas", "Gas"],
  ["water", "Agua"],
  ["internet", "Internet"],
  ["phone", "Telefonia"],
  ["home_insurance", "Seguro hogar"],
  ["rent_mortgage", "Alquiler / hipoteca"],
  ["community", "Comunidad"],
] as const;

const EMPTY_FORM: HouseholdBillCreate = {
  provider: "",
  service_type: "electricity",
  period_start: new Date().toISOString().slice(0, 10),
  period_end: new Date().toISOString().slice(0, 10),
  amount: "",
  currency: "EUR",
  is_recurring: true,
};

const serviceLabel = (value: string) => SERVICE_OPTIONS.find(([key]) => key === value)?.[1] ?? value;

export default function HouseholdBillsTab() {
  const { bills, summary, loading, error, add, remove } = useHouseholdBills();
  // El summary del backend agrega importes sin divisa; usamos la de las facturas.
  const billsCurrency = bills[0]?.currency ?? "EUR";
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<HouseholdBillCreate>(EMPTY_FORM);
  const [saving, setSaving] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaving(true);
    try {
      await add(form);
      setForm(EMPTY_FORM);
      setShowForm(false);
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <div className="rounded-lg border border-hairline-dark bg-white/[.03] p-8 text-center text-sm text-stone">Cargando facturas del hogar...</div>;
  if (error) return <div className="rounded-lg border border-accent-danger/30 bg-accent-danger/5 p-5 text-sm text-accent-danger">{error}</div>;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-on-dark">Facturas y suministros</h2>
          <p className="mt-1 text-sm text-stone">Registro manual local para luz, gas, agua, internet, telefonia, seguros, alquiler o comunidad.</p>
        </div>
        <button onClick={() => setShowForm((value) => !value)} className="inline-flex items-center gap-2 rounded-lg bg-primary px-3 py-2 text-xs font-medium text-white hover:bg-primary/90">
          <Plus size={14} />
          Registrar factura
        </button>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <section className="rounded-lg border border-hairline-dark bg-surface-card p-5">
          <Home size={18} className="text-primary-bright" />
          <p className="mt-3 text-xs text-stone">Estimacion proximo mes</p>
          <p className="financial-number mt-1 text-2xl text-on-dark">{formatCurrency(summary?.total_monthly_estimate ?? 0, billsCurrency)}</p>
        </section>
        <section className="rounded-lg border border-hairline-dark bg-surface-card p-5">
          <p className="text-xs text-stone">Servicios controlados</p>
          <p className="financial-number mt-1 text-2xl text-on-dark">{summary?.items.length ?? 0}</p>
          <p className="mt-2 text-xs text-stone">Agrupados por proveedor y tipo.</p>
        </section>
        <section className="rounded-lg border border-amber-400/25 bg-amber-400/10 p-5">
          <p className="text-xs text-amber-200">Subidas anomalas</p>
          <p className="financial-number mt-1 text-2xl text-on-dark">{summary?.items.filter((item) => item.anomaly).length ?? 0}</p>
          <p className="mt-2 text-xs text-stone">Marcadas si suben un 20% o mas frente al recibo anterior.</p>
        </section>
      </div>

      {showForm && (
        <form onSubmit={submit} className="rounded-lg border border-hairline-dark bg-surface-card p-5">
          <div className="grid gap-3 md:grid-cols-4">
            <label className="space-y-1"><span className="text-xs text-stone">Proveedor</span><input required value={form.provider} onChange={(e) => setForm((prev) => ({ ...prev, provider: e.target.value }))} className="w-full rounded-lg border border-hairline-dark bg-white/[.035] px-3 py-2 text-sm text-on-dark" /></label>
            <label className="space-y-1"><span className="text-xs text-stone">Servicio</span><select value={form.service_type} onChange={(e) => setForm((prev) => ({ ...prev, service_type: e.target.value }))} className="w-full rounded-lg border border-hairline-dark bg-white/[.035] px-3 py-2 text-sm text-on-dark">{SERVICE_OPTIONS.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
            <label className="space-y-1"><span className="text-xs text-stone">Inicio periodo</span><input required type="date" value={form.period_start} onChange={(e) => setForm((prev) => ({ ...prev, period_start: e.target.value }))} className="w-full rounded-lg border border-hairline-dark bg-white/[.035] px-3 py-2 text-sm text-on-dark" /></label>
            <label className="space-y-1"><span className="text-xs text-stone">Fin periodo</span><input required type="date" value={form.period_end} onChange={(e) => setForm((prev) => ({ ...prev, period_end: e.target.value }))} className="w-full rounded-lg border border-hairline-dark bg-white/[.035] px-3 py-2 text-sm text-on-dark" /></label>
            <label className="space-y-1"><span className="text-xs text-stone">Importe</span><input required type="number" step="0.01" value={form.amount} onChange={(e) => setForm((prev) => ({ ...prev, amount: e.target.value }))} className="w-full rounded-lg border border-hairline-dark bg-white/[.035] px-3 py-2 text-sm text-on-dark" /></label>
            <label className="space-y-1"><span className="text-xs text-stone">Vencimiento</span><input type="date" value={form.due_date ?? ""} onChange={(e) => setForm((prev) => ({ ...prev, due_date: e.target.value || null }))} className="w-full rounded-lg border border-hairline-dark bg-white/[.035] px-3 py-2 text-sm text-on-dark" /></label>
            <label className="flex items-center gap-2 pt-6 text-sm text-stone"><input type="checkbox" checked={form.is_recurring ?? true} onChange={(e) => setForm((prev) => ({ ...prev, is_recurring: e.target.checked }))} /> Recurrente</label>
          </div>
          <div className="mt-4 flex justify-end gap-2">
            <button type="button" onClick={() => setShowForm(false)} className="rounded-lg border border-hairline-dark px-4 py-2 text-sm text-stone">Cancelar</button>
            <button type="submit" disabled={saving} className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white disabled:opacity-50">{saving ? "Guardando..." : "Guardar"}</button>
          </div>
        </form>
      )}

      <div className="grid gap-4 lg:grid-cols-[1fr_.9fr]">
        <section className="rounded-lg border border-hairline-dark bg-surface-card p-5">
          <h3 className="text-sm font-semibold text-on-dark">Resumen por proveedor</h3>
          <div className="mt-4 space-y-3">
            {summary?.items.length ? summary.items.map((item) => (
              <div key={`${item.service_type}-${item.provider}`} className="rounded-lg border border-hairline-dark bg-white/[.03] p-3">
                <div className="flex items-center justify-between gap-3">
                  <div><p className="text-sm text-on-dark">{serviceLabel(item.service_type)} · {item.provider}</p><p className="text-xs text-stone">{item.bills_count} facturas · {item.latest_period}</p></div>
                  <div className="text-right"><p className="financial-number text-sm text-on-dark">{formatCurrency(item.next_estimate, billsCurrency)}</p><p className={item.anomaly ? "text-xs text-amber-200" : "text-xs text-stone"}>{item.change_pct == null ? "Sin comparativa" : `${item.change_pct}% vs anterior`}</p></div>
                </div>
              </div>
            )) : <p className="text-sm text-stone">Registra la primera factura para ver comparativas.</p>}
          </div>
        </section>

        <section className="rounded-lg border border-hairline-dark bg-surface-card p-5">
          <h3 className="text-sm font-semibold text-on-dark">Ultimas facturas</h3>
          <div className="mt-4 space-y-2">
            {bills.slice(0, 8).map((bill) => (
              <div key={bill.id} className="flex items-center justify-between gap-3 rounded-lg bg-white/[.03] px-3 py-2">
                <div><p className="text-sm text-on-dark">{serviceLabel(bill.service_type)} · {bill.provider}</p><p className="text-xs text-stone">{bill.period_start} - {bill.period_end}</p></div>
                <div className="flex items-center gap-3"><span className="financial-number text-sm text-on-dark">{formatCurrency(bill.amount, bill.currency)}</span><button onClick={() => remove(bill.id)} className="text-stone hover:text-accent-danger" aria-label={`Eliminar factura ${bill.provider}`}><Trash2 size={14} /></button></div>
              </div>
            ))}
            {!bills.length && <p className="text-sm text-stone">Sin facturas registradas.</p>}
          </div>
        </section>
      </div>
    </div>
  );
}
