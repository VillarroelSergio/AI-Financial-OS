import { useEffect, useState } from "react";
import { Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import Spinner from "@/components/ui/Spinner";
import { getHoldingPerformance, type HoldingPerformance } from "@/lib/api/investments";

// Mismos colores de estado ganancia/perdida que MiniSparkline (paleta validada)
const GAIN_COLOR = "var(--positive)";
const LOSS_COLOR = "var(--negative)";
const ENTRY_COLOR = "#a8adb3";

const DATE_LABEL = new Intl.DateTimeFormat("es-ES", { month: "short", year: "2-digit" });
const DATE_FULL = new Intl.DateTimeFormat("es-ES", { day: "2-digit", month: "short", year: "numeric" });

interface Props {
  holdingId: string;
}

export default function PositionEvolutionChart({ holdingId }: Props) {
  const [data, setData] = useState<HoldingPerformance | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setData(null);
    setError(null);
    getHoldingPerformance(holdingId)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "No se pudo cargar el histórico"));
  }, [holdingId]);

  if (error) {
    return <p className="text-sm text-amber-400/80 py-4">{error}</p>;
  }

  if (!data) {
    return (
      <div className="flex justify-center py-10">
        <Spinner />
      </div>
    );
  }

  const positive = (data.change_pct ?? 0) >= 0;
  const lineColor = positive ? GAIN_COLOR : LOSS_COLOR;
  const entryLabel = DATE_FULL.format(new Date(`${data.entry_date}T00:00:00`));

  return (
    <div>
      <div className="flex flex-wrap items-baseline gap-x-6 gap-y-1 mb-3">
        <p className="text-sm font-medium text-on-dark">
          {data.name} <span className="text-stone font-mono text-xs ml-1">{data.ticker}</span>
        </p>
        <p className="text-xs text-stone">
          Entrada: <span className="font-mono text-on-dark">{data.entry_price.toFixed(2)} {data.currency}</span> el {entryLabel}
          {data.entry_source === "holding" && " (fecha de alta, sin operación de compra registrada)"}
        </p>
        {data.change_pct !== null && (
          <p className="text-xs font-mono" style={{ color: lineColor }}>
            {positive ? "+" : ""}
            {data.change_pct.toFixed(2)}% desde la entrada
          </p>
        )}
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data.series} margin={{ top: 8, right: 16, bottom: 4, left: 4 }}>
            <XAxis
              dataKey="date"
              tick={{ fill: "#a8adb3", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              minTickGap={48}
              tickFormatter={(d: string) => DATE_LABEL.format(new Date(`${d}T00:00:00`))}
            />
            <YAxis
              domain={["auto", "auto"]}
              tick={{ fill: "#a8adb3", fontSize: 11 }}
              axisLine={false}
              tickLine={false}
              width={64}
              tickFormatter={(v: number) => `${v.toFixed(0)} ${data.currency}`}
            />
            <Tooltip
              formatter={(value) => [`${Number(value).toFixed(2)} ${data.currency}`, "Precio"]}
              labelFormatter={(label) => DATE_FULL.format(new Date(`${label}T00:00:00`))}
              contentStyle={{ background: "#16181a", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 8, color: "#fff", fontSize: 12 }}
            />
            <ReferenceLine
              y={data.entry_price}
              stroke={ENTRY_COLOR}
              strokeDasharray="4 4"
              ifOverflow="extendDomain"
              label={{ value: "Entrada", position: "insideTopRight", fill: ENTRY_COLOR, fontSize: 11 }}
            />
            <Line type="monotone" dataKey="price" stroke={lineColor} strokeWidth={2} dot={false} isAnimationActive={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
