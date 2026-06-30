import { RefreshCw } from "lucide-react";
import CompletenessDonut from "./CompletenessDonut";
import ConcentrationAlertCard from "./ConcentrationAlertCard";
import ReconciliationTable from "./ReconciliationTable";
import WeightBreakdownChart from "./WeightBreakdownChart";
import { useReconciliation } from "@/lib/hooks/useInvestments";

export default function ReconciliationTab() {
  const { data, loading, error, refresh } = useReconciliation();

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <RefreshCw size={20} className="animate-spin text-stone" />
        <span className="ml-2 text-sm text-stone">Calculando calidad de cartera...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-64 flex-col items-center justify-center gap-3">
        <p className="text-sm text-accent-danger">{error}</p>
        <button onClick={refresh} className="rounded-lg bg-white/5 px-4 py-2 text-sm text-on-dark hover:bg-white/8 transition-colors">
          Reintentar
        </button>
      </div>
    );
  }

  if (!data) return null;

  const kpis = [
    {
      label: "Valor total",
      value: data.portfolio_value_eur.toLocaleString("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }),
    },
    {
      label: "Confirmado",
      value: `${data.completeness.confirmed_pct.toFixed(1)}%`,
    },
    {
      label: "Alertas",
      value: String(data.concentration_alerts.length),
    },
    {
      label: "Posiciones",
      value: String(data.holdings.length),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-on-dark">Calidad de cartera</h2>
          <p className="mt-1 text-xs text-stone">Confirma que parte esta validada, estimada, manual, sin precio o pendiente de FX.</p>
          <p className="text-xs text-stone">
            Generado {new Date(data.generated_at).toLocaleString("es-ES")}
          </p>
        </div>
        <button
          onClick={refresh}
          className="flex items-center gap-1.5 rounded-lg bg-white/5 px-3 py-2 text-xs text-stone hover:text-on-dark hover:bg-white/8 transition-colors"
        >
          <RefreshCw size={13} />
          Actualizar
        </button>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {kpis.map((kpi) => (
          <div key={kpi.label} className="rounded-xl bg-surface-elevated p-4">
            <p className="text-[11px] uppercase tracking-wide text-stone">{kpi.label}</p>
            <p className="mt-1.5 text-xl font-semibold text-on-dark">{kpi.value}</p>
          </div>
        ))}
      </div>

      {/* Donut + breakdown */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="rounded-xl bg-surface-elevated p-5">
          <p className="mb-4 text-sm font-medium text-on-dark">Calidad de datos</p>
          <CompletenessDonut completeness={data.completeness} />
        </div>
        <div className="rounded-xl bg-surface-elevated p-5">
          <p className="mb-4 text-sm font-medium text-on-dark">Distribucion</p>
          <WeightBreakdownChart weightsBy={data.weights_by} />
        </div>
      </div>

      {/* Concentration alerts */}
      {data.concentration_alerts.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-on-dark">Alertas de concentracion</p>
          {data.concentration_alerts.map((alert, i) => (
            <ConcentrationAlertCard key={i} alert={alert} />
          ))}
        </div>
      )}

      {/* Holdings table */}
      <div className="rounded-xl bg-surface-elevated">
        <div className="border-b border-white/8 px-5 py-4">
          <p className="text-sm font-medium text-on-dark">Posiciones ({data.holdings.length})</p>
        </div>
        <ReconciliationTable holdings={data.holdings} />
      </div>
    </div>
  );
}
