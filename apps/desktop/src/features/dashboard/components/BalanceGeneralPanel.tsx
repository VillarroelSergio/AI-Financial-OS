import { ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { useBalanceSheet, useSnapshots } from "@/lib/hooks/useNetWorth";
import { formatCurrency } from "@/lib/formatters/currency";

export default function BalanceGeneralPanel() {
  const [open, setOpen] = useState(true);
  const { data: sheet, loading } = useBalanceSheet();
  const { data: snapshots } = useSnapshots();
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
            <div className="flex items-baseline justify-between rounded-lg bg-[var(--bg-card-elevated)] px-4 py-3">
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
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--divider-soft)" />
                  <XAxis dataKey="month" tick={{ fontSize: 11, fill: "var(--text-secondary)" }} />
                  <YAxis tick={{ fontSize: 11, fill: "var(--text-secondary)" }} width={60} />
                  <Tooltip
                    formatter={(v) => formatCurrency(Number(v))}
                    contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border-soft)", borderRadius: 8, color: "var(--text-primary)" }}
                  />
                  <Line type="monotone" dataKey="net_worth" stroke="var(--primary)" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}

        </div>
      )}
    </div>
  );
}
