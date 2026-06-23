import MetricCard from "@/components/ui/MetricCard";
import Spinner from "@/components/ui/Spinner";
import { useOverview } from "@/lib/hooks/useDashboard";
import { formatCurrency, formatPercent } from "@/lib/formatters/currency";

export default function OverviewPage() {
  const { data, loading } = useOverview();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Spinner />
      </div>
    );
  }

  const d = data ?? {
    net_worth: "0",
    liquidity: "0",
    investments: "0",
    monthly_income: "0",
    monthly_expense: "0",
    monthly_savings: "0",
    savings_rate: 0,
    currency: "EUR",
  };

  const savings = parseFloat(d.monthly_savings);

  return (
    <div className="p-2xl space-y-xl">
      <div>
        <h1 className="text-display-lg text-on-dark">Resumen</h1>
        <p className="text-body-sm text-stone mt-xs">Tu situación financiera actual</p>
      </div>

      <div className="grid grid-cols-3 gap-lg">
        <MetricCard label="Patrimonio neto" value={formatCurrency(d.net_worth)} />
        <MetricCard label="Liquidez" value={formatCurrency(d.liquidity)} />
        <MetricCard label="Inversiones" value={formatCurrency(d.investments)} />
      </div>

      <div className="grid grid-cols-3 gap-lg">
        <MetricCard
          label="Ingresos del mes"
          value={formatCurrency(d.monthly_income)}
          deltaPositive
        />
        <MetricCard label="Gastos del mes" value={formatCurrency(d.monthly_expense)} />
        <MetricCard
          label="Ahorro del mes"
          value={formatCurrency(d.monthly_savings)}
          delta={`Tasa de ahorro: ${formatPercent(d.savings_rate)}`}
          deltaPositive={savings >= 0}
        />
      </div>
    </div>
  );
}
