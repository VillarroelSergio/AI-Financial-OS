import { useEffect, useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { getPortfolioEvolution, type PortfolioEvolutionPoint } from "@/lib/api/investments";

const LINE_COLOR = "#5B7EA3";
const DATE_LABEL = new Intl.DateTimeFormat("es-ES", { month: "short", year: "2-digit" });
const monthLabel = (m: string) => DATE_LABEL.format(new Date(`${m}-01T00:00:00`));

/** Evolución agregada del valor de la cartera (fondos + cuentas + mercado). INV-6. */
export default function PortfolioEvolutionChart() {
  const [series, setSeries] = useState<PortfolioEvolutionPoint[] | null>(null);

  useEffect(() => {
    let alive = true;
    getPortfolioEvolution()
      .then((r) => { if (alive) setSeries(r.series); })
      .catch(() => { if (alive) setSeries([]); });
    return () => { alive = false; };
  }, []);

  if (series === null) return null;
  if (series.length < 2) {
    return (
      <div className="bg-surface-card border border-hairline-dark rounded-md p-xl">
        <p className="text-body-sm text-on-dark mb-xs">Evolución de la cartera</p>
        <p className="text-caption text-stone">
          Aún no hay suficientes valoraciones para dibujar la evolución. Añade snapshots de fondos o histórico de precios.
        </p>
      </div>
    );
  }

  const data = series.map((p) => ({ month: p.month, value: p.value }));

  return (
    <div className="bg-surface-card border border-hairline-dark rounded-md p-xl">
      <p className="text-body-sm text-on-dark mb-md">Evolución de la cartera</p>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 4, left: 4 }}>
            <defs>
              <linearGradient id="portfolioFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={LINE_COLOR} stopOpacity={0.35} />
                <stop offset="100%" stopColor={LINE_COLOR} stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
            <XAxis
              dataKey="month"
              tick={{ fill: "#a8adb3", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              minTickGap={40}
              tickFormatter={monthLabel}
            />
            <YAxis
              tick={{ fill: "#a8adb3", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={64}
              tickFormatter={(v: number) => `${v.toFixed(0)} €`}
            />
            <Tooltip
              labelFormatter={(label) => monthLabel(String(label))}
              formatter={(value) => [`${Number(value).toFixed(2)} €`, "Valor"]}
              contentStyle={{ background: "#16181a", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 8, color: "#fff", fontSize: 12 }}
            />
            <Area type="monotone" dataKey="value" stroke={LINE_COLOR} strokeWidth={2} fill="url(#portfolioFill)" isAnimationActive={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
