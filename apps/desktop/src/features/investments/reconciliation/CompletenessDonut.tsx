import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import type { ReconciliationReport } from "@/lib/api/investments";

const SEGMENTS = [
  { key: "confirmed_pct",  label: "Confirmado",  color: "#2F8F6B" },
  { key: "estimated_pct",  label: "Estimado",    color: "#C28A4A" },
  { key: "manual_pct",     label: "Manual",      color: "#8d969e" },
  { key: "no_price_pct",   label: "Sin precio",  color: "#A97844" },
] as const;

interface Props {
  completeness: ReconciliationReport["completeness"];
}

export default function CompletenessDonut({ completeness }: Props) {
  const data = SEGMENTS.map((s) => ({
    name: s.label,
    value: completeness[s.key],
    color: s.color,
  })).filter((d) => d.value > 0);

  const confirmedPct = completeness.confirmed_pct;

  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative h-48 w-48">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={56}
              outerRadius={80}
              dataKey="value"
              strokeWidth={0}
            >
              {data.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{ background: "#16181a", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 8 }}
              itemStyle={{ color: "#fff", fontSize: 12 }}
              formatter={(value: unknown) => [`${(value as number).toFixed(1)}%`, ""]}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <p className="text-2xl font-semibold text-on-dark">{confirmedPct.toFixed(0)}%</p>
          <p className="text-[11px] text-stone">validado</p>
        </div>
      </div>
      <div className="flex flex-wrap justify-center gap-x-4 gap-y-1.5">
        {SEGMENTS.map((s) => (
          <div key={s.key} className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full flex-shrink-0" style={{ background: s.color }} />
            <span className="text-[11px] text-stone">{s.label} {completeness[s.key].toFixed(1)}%</span>
          </div>
        ))}
      </div>
    </div>
  );
}
