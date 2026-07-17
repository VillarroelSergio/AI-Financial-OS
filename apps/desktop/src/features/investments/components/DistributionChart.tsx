import { useMemo, useState } from "react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { formatCurrency } from "@/lib/formatters/currency";
import type { HoldingEnriched } from "@/lib/types";

const COLORS = ["#5b5ef7", "var(--positive)", "#f59e0b", "#38bdf8", "#a78bfa", "var(--negative)", "#9CB39A"];
type View = "asset" | "broker" | "type" | "currency" | "sector";

const VIEWS: { key: View; label: string }[] = [
  { key: "asset", label: "Por activo" },
  { key: "broker", label: "Por broker" },
  { key: "type", label: "Por tipo" },
  { key: "currency", label: "Por divisa" },
  { key: "sector", label: "Por sector" },
];

interface DistributionChartProps {
  holdings: HoldingEnriched[];
  accountNames: Record<string, string>;
}

export default function DistributionChart({ holdings, accountNames }: DistributionChartProps) {
  const [view, setView] = useState<View>("asset");
  const rows = useMemo(() => {
    const groups = new Map<string, number>();
    holdings.filter((h) => !h.is_mock).forEach((holding) => {
      const value = Number(holding.market_value ?? 0);
      const key =
        view === "asset" ? holding.display_name :
        view === "broker" ? accountNames[holding.account_id] ?? "Broker sin nombre" :
        view === "type" ? holding.asset_type :
        view === "currency" ? holding.currency :
        holding.asset.sector || "Sin sector";
      groups.set(key, (groups.get(key) ?? 0) + value);
    });
    const total = Array.from(groups.values()).reduce((sum, value) => sum + value, 0);
    const sorted = Array.from(groups.entries())
      .map(([name, value], index) => ({ name, value, pct: total > 0 ? (value / total) * 100 : 0, color: COLORS[index % COLORS.length] }))
      .sort((a, b) => b.value - a.value);
    if (sorted.length <= 6) return sorted;
    const visible = sorted.slice(0, 5);
    const other = sorted.slice(5).reduce((sum, item) => sum + item.value, 0);
    return [...visible, { name: "Otros", value: other, pct: total > 0 ? (other / total) * 100 : 0, color: COLORS[5] }];
  }, [accountNames, holdings, view]);

  const total = rows.reduce((sum, item) => sum + item.value, 0);
  const useBars = view === "asset" || rows.length > 6;

  return (
    <div className="bg-surface-card border border-hairline-dark rounded-md p-xl">
      <div className="flex items-start justify-between gap-lg mb-lg">
        <div>
          <h2 className="text-heading-sm text-on-dark">Distribucion de cartera</h2>
          <p className="text-caption text-stone mt-xs">Importes reales; datos demo excluidos del reparto.</p>
        </div>
        <div className="flex flex-wrap gap-xs justify-end">
          {VIEWS.map((item) => (
            <button key={item.key} onClick={() => setView(item.key)} className={`rounded-full px-sm py-xs text-caption ${view === item.key ? "bg-primary text-on-primary" : "bg-surface-elevated text-stone hover:text-on-dark"}`}>
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {rows.length === 0 || total <= 0 ? (
        <div className="rounded-md border border-hairline-dark bg-surface-elevated p-lg text-center text-body-sm text-stone">
          No hay importes reales suficientes para calcular la distribucion.
        </div>
      ) : useBars ? (
        <div className="space-y-md">
          {rows.map((entry) => (
            <div key={`${view}-${entry.name}`}>
              <div className="flex items-center justify-between gap-md text-body-sm">
                <span className="min-w-0 truncate text-on-dark">{entry.name}</span>
                <span className="financial-number shrink-0 text-stone">{formatCurrency(entry.value)} · {entry.pct.toFixed(1)}%</span>
              </div>
              <div className="mt-xs h-2 rounded-full bg-[var(--bg-interactive)] overflow-hidden">
                <div className="portfolio-allocation-bar h-full rounded-full" style={{ width: `${Math.max(2, entry.pct)}%`, background: entry.color }} />
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-[190px_1fr] items-center gap-xl">
          <ResponsiveContainer width="100%" height={190}>
            <PieChart>
              <Pie data={rows} dataKey="value" nameKey="name" cx="50%" cy="50%" innerRadius={58} outerRadius={86} paddingAngle={2}>
                {rows.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
              </Pie>
              <Tooltip formatter={(value) => [formatCurrency(Number(value)), "Valor"]} contentStyle={{ background: "#16181a", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 8, color: "#fff", fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-sm">
            {rows.map((entry) => (
              <div key={entry.name} className="flex items-center justify-between gap-md">
                <div className="flex items-center gap-sm min-w-0">
                  <span className="h-2.5 w-2.5 rounded-full shrink-0" style={{ background: entry.color }} />
                  <span className="text-body-sm text-on-dark truncate">{entry.name}</span>
                </div>
                <span className="financial-number text-caption text-stone shrink-0">{formatCurrency(entry.value)} · {entry.pct.toFixed(1)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
