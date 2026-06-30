import { RefreshCw } from "lucide-react";
import CashflowChart from "./CashflowChart";
import { useCashflowForecast } from "@/lib/hooks/useBudgets";

export default function CashflowTab() {
  const { data, loading, error, refresh } = useCashflowForecast(3);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <RefreshCw size={20} className="animate-spin text-stone" />
        <span className="ml-2 text-sm text-stone">Calculando previsión...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3">
        <p className="text-sm text-accent-danger">{error}</p>
        <button onClick={refresh} className="rounded-lg bg-white/5 px-4 py-2 text-sm text-on-dark">Reintentar</button>
      </div>
    );
  }

  if (!data || data.months.length === 0) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3">
        <p className="text-sm text-stone">Añade transacciones recurrentes para mejorar la previsión.</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-on-dark">Previsión de cashflow</h2>
        <button onClick={refresh} className="flex items-center gap-1.5 rounded-lg bg-white/5 px-3 py-2 text-xs text-stone hover:text-on-dark transition-colors">
          <RefreshCw size={13} />
          Actualizar
        </button>
      </div>

      <div className="rounded-xl bg-surface-elevated p-5">
        <p className="mb-4 text-sm font-medium text-on-dark">Proyección mensual</p>
        <CashflowChart months={data.months} />
      </div>

      <div className="rounded-xl bg-surface-elevated overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-white/8">
              <th className="px-4 py-3 text-left text-[11px] font-medium uppercase tracking-wide text-stone">Mes</th>
              <th className="px-4 py-3 text-right text-[11px] font-medium uppercase tracking-wide text-stone">Ingresos</th>
              <th className="px-4 py-3 text-right text-[11px] font-medium uppercase tracking-wide text-stone">Gastos</th>
              <th className="px-4 py-3 text-right text-[11px] font-medium uppercase tracking-wide text-stone">Saldo</th>
            </tr>
          </thead>
          <tbody>
            {data.months.map(m => (
              <tr key={m.month} className="border-b border-white/4">
                <td className="px-4 py-3 text-on-dark">{m.month}</td>
                <td className="px-4 py-3 text-right text-accent-teal">{m.projected_income.toLocaleString("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 })}</td>
                <td className="px-4 py-3 text-right text-accent-danger">{m.projected_expenses.toLocaleString("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 })}</td>
                <td className={["px-4 py-3 text-right font-medium", m.projected_balance >= 0 ? "text-accent-teal" : "text-accent-danger"].join(" ")}>
                  {m.projected_balance >= 0 ? "+" : ""}{m.projected_balance.toLocaleString("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 })}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
