import { ChevronDown, ChevronRight } from "lucide-react";
import { useState } from "react";
import { useBalanceSheet } from "@/lib/hooks/useNetWorth";
import { formatCurrency } from "@/lib/formatters/currency";

function currentMonth(): string {
  return new Date().toISOString().slice(0, 7);
}

/** Balance actual, sin flujos de cierre. */
export default function BalanceGeneralPanel() {
  const [open, setOpen] = useState(true);
  const { data: sheet, loading } = useBalanceSheet(currentMonth());

  return (
    <section className="premium-card rounded-lg">
      <button
        type="button"
        onClick={() => setOpen((value) => !value)}
        className="flex w-full items-center justify-between p-5"
        aria-expanded={open}
      >
        <span className="flex items-center gap-2 font-semibold">
          {open ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
          Balance general
        </span>
        <span className="text-caption text-stone">Situación actual</span>
      </button>

      {open && (
        <div className="space-y-5 px-5 pb-5">
          {loading && <div className="py-4 text-body-sm text-stone">Cargando balance…</div>}

          {sheet && (
            <>
              <div className="grid gap-5 md:grid-cols-2">
                <div>
                  <p className="mb-1 text-caption font-semibold uppercase tracking-wide text-stone">Activos</p>
                  {sheet.assets.map((asset) => (
                    <div key={asset.key} className="flex justify-between py-1 text-body-sm">
                      <span>{asset.label}</span>
                      <span className="financial-number">{formatCurrency(asset.amount)}</span>
                    </div>
                  ))}
                  <div className="mt-1 flex justify-between border-t border-divider-soft pt-1 text-body-sm font-semibold">
                    <span>Total activos</span>
                    <span className="financial-number text-accent-teal">{formatCurrency(sheet.total_assets)}</span>
                  </div>
                </div>

                <div>
                  <p className="mb-1 text-caption font-semibold uppercase tracking-wide text-stone">Pasivos</p>
                  {sheet.liabilities.length === 0 && <p className="py-1 text-body-sm text-stone">Sin pasivos registrados.</p>}
                  {sheet.liabilities.map((liability) => (
                    <div key={liability.key} className="flex justify-between py-1 text-body-sm">
                      <span>{liability.label}</span>
                      <span className="financial-number text-accent-danger">−{formatCurrency(liability.amount)}</span>
                    </div>
                  ))}
                  <div className="mt-1 flex justify-between border-t border-divider-soft pt-1 text-body-sm font-semibold">
                    <span>Total pasivos</span>
                    <span className="financial-number text-accent-danger">{formatCurrency(sheet.total_liabilities)}</span>
                  </div>
                </div>
              </div>

              <div className="flex items-baseline justify-between rounded-lg bg-black/20 px-4 py-3">
                <span className="text-body-sm font-semibold">Patrimonio neto</span>
                <span className="flex items-baseline gap-3">
                  <span className="financial-number text-lg font-semibold">{formatCurrency(sheet.net_worth)}</span>
                  {sheet.net_worth_change !== null && (
                    <span className={`text-body-sm ${Number(sheet.net_worth_change) >= 0 ? "text-accent-teal" : "text-accent-danger"}`}>
                      {Number(sheet.net_worth_change) >= 0 ? "+" : ""}{formatCurrency(sheet.net_worth_change)}
                    </span>
                  )}
                </span>
              </div>
            </>
          )}
        </div>
      )}
    </section>
  );
}
