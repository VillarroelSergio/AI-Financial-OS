import {
  Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from "recharts";
import type { MonthForecast } from "@/lib/api/budgets";

interface Props {
  months: MonthForecast[];
}

export default function CashflowChart({ months }: Props) {
  const data = months.map(m => ({
    name: m.month.slice(0, 7),
    ingresos: m.projected_income,
    gastos: m.projected_expenses,
    balance: m.projected_balance,
  }));

  return (
    <div className="h-56">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ left: 8, right: 8 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="name" tick={{ fill: "#8d969e", fontSize: 11 }} axisLine={false} tickLine={false} />
          <YAxis tick={{ fill: "#8d969e", fontSize: 11 }} axisLine={false} tickLine={false} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
          <Tooltip
            contentStyle={{ background: "#16181a", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 8 }}
            itemStyle={{ color: "#fff", fontSize: 12 }}
            formatter={(value: unknown) => [(value as number).toLocaleString("es-ES", { style: "currency", currency: "EUR" }), ""]}
          />
          <Legend wrapperStyle={{ fontSize: 11, color: "#8d969e" }} />
          <Bar dataKey="ingresos" name="Ingresos" fill="#2F8F6B" radius={[4, 4, 0, 0]} />
          <Bar dataKey="gastos" name="Gastos" fill="#C95B66" radius={[4, 4, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
