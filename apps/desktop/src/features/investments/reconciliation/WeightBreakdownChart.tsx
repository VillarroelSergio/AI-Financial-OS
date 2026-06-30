import { useState } from "react";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ReconciliationReport } from "@/lib/api/investments";

type Dimension = keyof ReconciliationReport["weights_by"];

const TABS: { key: Dimension; label: string }[] = [
  { key: "currency",   label: "Divisa" },
  { key: "sector",     label: "Sector" },
  { key: "broker",     label: "Broker" },
  { key: "asset_type", label: "Tipo" },
  { key: "region",     label: "Region" },
];

interface Props {
  weightsBy: ReconciliationReport["weights_by"];
}

export default function WeightBreakdownChart({ weightsBy }: Props) {
  const [active, setActive] = useState<Dimension>("currency");
  const data = (weightsBy[active] ?? []).slice(0, 8);

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-1.5">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActive(tab.key)}
            className={[
              "rounded-full px-3 py-1.5 text-xs font-medium transition-colors",
              active === tab.key
                ? "bg-primary text-white"
                : "bg-white/5 text-stone hover:text-on-dark",
            ].join(" ")}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {data.length === 0 ? (
        <p className="py-8 text-center text-sm text-stone">Sin datos para esta dimension.</p>
      ) : (
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data} layout="vertical" margin={{ left: 8, right: 24 }}>
              <XAxis
                type="number"
                domain={[0, 100]}
                tickFormatter={(v) => `${v}%`}
                tick={{ fill: "#8d969e", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                type="category"
                dataKey="key"
                width={80}
                tick={{ fill: "#8d969e", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{ background: "#16181a", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 8 }}
                itemStyle={{ color: "#fff", fontSize: 12 }}
                formatter={(value) => {
                  if (typeof value === "number") {
                    return [`${value.toFixed(1)}%`, "Peso"];
                  }
                  return value;
                }}
                cursor={{ fill: "rgba(255,255,255,0.04)" }}
              />
              <Bar dataKey="weight_pct" radius={[0, 4, 4, 0]}>
                {data.map((_, i) => (
                  <Cell key={i} fill="#494fdf" fillOpacity={1 - i * 0.08} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
