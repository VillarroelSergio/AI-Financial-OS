import { AlertTriangle, Check, ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { createSnapshot, useBalanceSheet, useReadiness, useSnapshots } from "@/lib/hooks/useNetWorth";
import type { ReadinessItem, ReadinessStatus } from "@/lib/api/net-worth";
import { formatCurrency } from "@/lib/formatters/currency";

function currentMonth(): string {
  return new Date().toISOString().slice(0, 7);
}

const STATUS_STYLE: Record<ReadinessStatus, { icon: typeof Check; cls: string; label: string }> = {
  ok: { icon: Check, cls: "text-accent-teal", label: "OK" },
  stale: { icon: AlertTriangle, cls: "text-accent-warning", label: "Desactualizado" },
  missing: { icon: AlertTriangle, cls: "text-accent-danger", label: "Falta" },
};

function ChecklistRow({ item }: { item: ReadinessItem }) {
  const navigate = useNavigate();
  const s = STATUS_STYLE[item.status];
  const Icon = s.icon;
  return (
    <div className="flex items-center justify-between border-t border-divider-soft py-2 text-sm first:border-0">
      <span className="flex items-center gap-2">
        <Icon size={15} className={s.cls} />
        <span>{item.label}</span>
        {item.detail && <span className="text-xs text-stone">— {item.detail}</span>}
      </span>
      {item.status !== "ok" && item.cta_route && (
        <button
          onClick={() => navigate(item.cta_route!)}
          className="shrink-0 text-xs text-primary-bright hover:underline"
        >
          Resolver
        </button>
      )}
    </div>
  );
}

export default function BalanceGeneralPanel() {
  const [open, setOpen] = useState(true);
  const [busy, setBusy] = useState(false);
  const month = currentMonth();
  const { data: sheet, loading } = useBalanceSheet(month);
  const { data: readiness, reload: reloadReadiness } = useReadiness(month);
  const { data: snapshots, reload: reloadSnapshots } = useSnapshots();

  async function close(forcePartial: boolean) {
    const msg = forcePartial
      ? "¿Cerrar el mes como PARCIAL? Se registrará qué información faltaba."
      : "¿Cerrar el mes y crear el snapshot de patrimonio?";
    if (!window.confirm(msg)) return;
    setBusy(true);
    try {
      await createSnapshot(month, forcePartial);
      await Promise.all([reloadReadiness(), reloadSnapshots()]);
    } catch (e) {
      window.alert(e instanceof Error ? e.message : "No se pudo cerrar el mes.");
    } finally {
      setBusy(false);
    }
  }

  const closed = readiness?.snapshot_exists ?? false;
  const chartData = (snapshots ?? []).map((s) => ({ month: s.month, net_worth: Number(s.net_worth) }));

  return (
    <div className="premium-card rounded-lg">
      <button
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between p-5"
      >
        <span className="flex items-center gap-2 font-semibold">
          {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          Balance General
        </span>
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs ${
            closed
              ? "bg-accent-teal/10 text-accent-teal"
              : "bg-accent-warning/10 text-accent-warning"
          }`}
        >
          {closed
            ? readiness?.snapshot_state === "partial"
              ? "Cerrado (parcial)"
              : "Cerrado"
            : "Pendiente de cierre"}
        </span>
      </button>

      {open && (
        <div className="space-y-5 px-5 pb-5">
          {loading && <div className="py-4 text-sm text-stone">Cargando balance…</div>}

          {sheet && (
            <div className="grid gap-5 md:grid-cols-2">
              <div>
                <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-stone">Activos</p>
                {sheet.assets.map((a) => (
                  <div key={a.key} className="flex justify-between py-1 text-sm">
                    <span>{a.label}</span>
                    <span className="financial-number">{formatCurrency(a.amount)}</span>
                  </div>
                ))}
                <div className="mt-1 flex justify-between border-t border-divider-soft pt-1 text-sm font-semibold">
                  <span>Total activos</span>
                  <span className="financial-number text-accent-teal">{formatCurrency(sheet.total_assets)}</span>
                </div>
              </div>

              <div>
                <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-stone">Pasivos</p>
                {sheet.liabilities.length === 0 && (
                  <p className="py-1 text-sm text-stone">Sin pasivos registrados.</p>
                )}
                {sheet.liabilities.map((l) => (
                  <div key={l.key} className="flex justify-between py-1 text-sm">
                    <span>{l.label}</span>
                    <span className="financial-number text-accent-danger">−{formatCurrency(l.amount)}</span>
                  </div>
                ))}
                <div className="mt-1 flex justify-between border-t border-divider-soft pt-1 text-sm font-semibold">
                  <span>Total pasivos</span>
                  <span className="financial-number text-accent-danger">{formatCurrency(sheet.total_liabilities)}</span>
                </div>
              </div>
            </div>
          )}

          {sheet && (
            <div className="flex items-baseline justify-between rounded-lg bg-black/20 px-4 py-3">
              <span className="text-sm font-semibold">Patrimonio neto</span>
              <span className="flex items-baseline gap-3">
                <span className="financial-number text-lg font-semibold">{formatCurrency(sheet.net_worth)}</span>
                {sheet.net_worth_change !== null && (
                  <span
                    className={`text-sm ${Number(sheet.net_worth_change) >= 0 ? "text-accent-teal" : "text-accent-danger"}`}
                  >
                    {Number(sheet.net_worth_change) >= 0 ? "+" : ""}
                    {formatCurrency(sheet.net_worth_change)}
                  </span>
                )}
              </span>
            </div>
          )}

          {chartData.length >= 2 && (
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff12" />
                  <XAxis dataKey="month" tick={{ fontSize: 11, fill: "#8a8f98" }} />
                  <YAxis tick={{ fontSize: 11, fill: "#8a8f98" }} width={60} />
                  <Tooltip
                    formatter={(v) => formatCurrency(Number(v))}
                    contentStyle={{ background: "#1a1a1f", border: "1px solid #ffffff20", borderRadius: 8 }}
                  />
                  <Line type="monotone" dataKey="net_worth" stroke="#2F8F6B" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

          {readiness && (
            <div className="rounded-lg border border-hairline-dark p-4">
              <p className="mb-2 text-sm font-semibold">
                Cierre de {month}
                {!readiness.ready && (
                  <span className="ml-2 text-xs font-normal text-stone">
                    {readiness.items.filter((i) => i.status === "ok").length} de {readiness.items.length} elementos actualizados
                  </span>
                )}
              </p>
              {readiness.items.map((i) => (
                <ChecklistRow key={i.key} item={i} />
              ))}
              <div className="mt-3 flex gap-2">
                <button
                  disabled={!readiness.ready || busy}
                  onClick={() => close(false)}
                  className="mercury-button-primary rounded-lg px-3 py-2 text-sm disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Cerrar mes y crear snapshot
                </button>
                <button
                  disabled={busy}
                  onClick={() => close(true)}
                  className="rounded-lg border border-hairline-dark px-3 py-2 text-sm text-stone hover:text-on-dark disabled:opacity-40"
                >
                  Cerrar como parcial
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
