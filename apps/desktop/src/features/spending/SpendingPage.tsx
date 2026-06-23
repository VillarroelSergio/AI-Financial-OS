import { useState } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import EmptyState from "@/components/ui/EmptyState";
import MetricCard from "@/components/ui/MetricCard";
import Spinner from "@/components/ui/Spinner";
import { useSpending } from "@/lib/hooks/useDashboard";
import { formatCurrency, formatPercent } from "@/lib/formatters/currency";

const CHART_COLORS = [
  "#494fdf",
  "#00a87e",
  "#ec7e00",
  "#e23b4a",
  "#b09000",
  "#8d969e",
  "#4f55f1",
  "#505a63",
];

function getCurrentMonth() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`;
}

export default function SpendingPage() {
  const [month, setMonth] = useState(getCurrentMonth);
  const { data, loading } = useSpending(month);

  const prevMonth = () => {
    const [y, m] = month.split("-").map(Number);
    const d = new Date(y, m - 2, 1);
    setMonth(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`);
  };

  const nextMonth = () => {
    const [y, m] = month.split("-").map(Number);
    const d = new Date(y, m, 1);
    setMonth(`${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`);
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner />
      </div>
    );
  }

  const hasCategoryData = data && data.by_category.length > 0;
  const chartData =
    data?.by_category.map((c) => ({ name: c.category, value: parseFloat(c.amount) })) ?? [];

  return (
    <div className="p-2xl space-y-xl">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-display-lg text-on-dark">Gastos</h1>
          <p className="text-body-sm text-stone mt-xs">Análisis de gastos mensual</p>
        </div>
        <div className="flex items-center gap-md">
          <button
            onClick={prevMonth}
            className="text-stone hover:text-on-dark text-heading-sm transition-colors px-sm"
          >
            ‹
          </button>
          <span className="text-body-md text-on-dark w-24 text-center">{month}</span>
          <button
            onClick={nextMonth}
            className="text-stone hover:text-on-dark text-heading-sm transition-colors px-sm"
          >
            ›
          </button>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-lg">
        <MetricCard label="Gasto total" value={formatCurrency(data?.total_expense ?? "0")} />
        <MetricCard
          label="Ingreso total"
          value={formatCurrency(data?.total_income ?? "0")}
          deltaPositive
        />
      </div>

      {!hasCategoryData ? (
        <EmptyState
          title="Sin datos"
          description="No hay gastos registrados para este mes."
        />
      ) : (
        <div className="grid grid-cols-2 gap-xl">
          <div className="bg-surface-card border border-hairline-dark rounded-md p-xl">
            <h2 className="text-heading-sm text-on-dark mb-xl">Por categoría</h2>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie
                  data={chartData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  paddingAngle={2}
                >
                  {chartData.map((_, i) => (
                    <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value) => [formatCurrency(Number(value)), "Importe"]}
                  contentStyle={{
                    background: "#1e2124",
                    border: "1px solid rgba(255,255,255,0.12)",
                    borderRadius: 8,
                    color: "#fff",
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-surface-card border border-hairline-dark rounded-md p-xl">
            <h2 className="text-heading-sm text-on-dark mb-xl">Desglose</h2>
            <div className="space-y-sm">
              {data?.by_category.map((cat, i) => (
                <div
                  key={cat.category_id ?? cat.category}
                  className="flex items-center justify-between"
                >
                  <div className="flex items-center gap-sm">
                    <span
                      className="w-2 h-2 rounded-full flex-shrink-0"
                      style={{ background: CHART_COLORS[i % CHART_COLORS.length] }}
                    />
                    <span className="text-body-sm text-on-dark">{cat.category}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-body-sm text-on-dark">{formatCurrency(cat.amount)}</span>
                    <span className="text-caption text-stone ml-sm">
                      {formatPercent(cat.percentage)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
