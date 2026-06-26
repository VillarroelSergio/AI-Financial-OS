import { Cell, Pie, PieChart, Tooltip } from "recharts";
import { formatCurrency } from "@/lib/formatters/currency";
import type { AccountSummary } from "@/lib/types";

const COLORS = ["#494fdf", "#00a87e", "#376cd5"];

interface DistributionChartProps {
  byAccount: AccountSummary[];
  accountNames: Record<string, string>;
}

export default function DistributionChart({ byAccount, accountNames }: DistributionChartProps) {
  const total = byAccount.reduce((s, a) => s + parseFloat(a.value), 0);
  const data = byAccount.map((a, i) => ({
    name: accountNames[a.account_id] ?? a.account_id,
    value: parseFloat(a.value),
    color: COLORS[i % COLORS.length],
  }));

  return (
    <div className="bg-surface-card border border-hairline-dark rounded-md p-xl">
      <h2 className="text-heading-sm text-on-dark mb-xl">Distribución de cartera</h2>
      <div className="flex items-center gap-xl">
        <div className="flex-shrink-0">
          <PieChart width={180} height={180}>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={55}
              outerRadius={85}
              paddingAngle={2}
            >
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value) => [formatCurrency(Number(value)), "Valor"]}
              contentStyle={{
                background: "#16181a",
                border: "1px solid rgba(255,255,255,0.12)",
                borderRadius: 8,
                color: "#fff",
                fontSize: 12,
              }}
            />
          </PieChart>
        </div>
        <div className="flex-1 space-y-sm">
          {data.map((entry) => (
            <div key={entry.name} className="flex items-center justify-between">
              <div className="flex items-center gap-sm">
                <span
                  className="w-2 h-2 rounded-full flex-shrink-0"
                  style={{ background: entry.color }}
                />
                <span className="text-body-sm text-on-dark">{entry.name}</span>
              </div>
              <div className="text-right">
                <span className="text-body-sm text-on-dark">
                  {formatCurrency(entry.value)}
                </span>
                <span className="text-caption text-stone ml-sm">
                  {total > 0 ? ((entry.value / total) * 100).toFixed(1) : "0.0"}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
