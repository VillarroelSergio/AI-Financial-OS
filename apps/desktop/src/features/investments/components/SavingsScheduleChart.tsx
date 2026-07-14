import { Bar, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { SavingsProjection } from "@/lib/api/investments";

const BALANCE_COLOR = "#5b5ef7";
const INTEREST_COLOR = "var(--positive)";
const DATE_LABEL = new Intl.DateTimeFormat("es-ES", { month: "short", year: "2-digit" });

const monthLabel = (m: string) => DATE_LABEL.format(new Date(`${m}-01T00:00:00`));

interface Props {
  schedule: SavingsProjection;
}

export default function SavingsScheduleChart({ schedule }: Props) {
  const data = schedule.points.map((p) => ({
    month: p.month,
    balance: Number(p.balance_end),
    interest: Number(p.interest),
  }));

  return (
    <div className="h-64">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data} margin={{ top: 8, right: 8, bottom: 4, left: 4 }}>
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
            yAxisId="balance"
            tick={{ fill: "#a8adb3", fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={64}
            tickFormatter={(v: number) => `${v.toFixed(0)} €`}
          />
          <YAxis yAxisId="interest" orientation="right" hide />
          <Tooltip
            labelFormatter={(label) => monthLabel(String(label))}
            formatter={(value, name) => [
              `${Number(value).toFixed(2)} €`,
              name === "balance" ? "Saldo" : "Interés del mes",
            ]}
            contentStyle={{ background: "#16181a", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 8, color: "#fff", fontSize: 12 }}
          />
          <Bar yAxisId="interest" dataKey="interest" fill={INTEREST_COLOR} opacity={0.55} isAnimationActive={false} />
          <Line yAxisId="balance" type="monotone" dataKey="balance" stroke={BALANCE_COLOR} strokeWidth={2} dot={false} isAnimationActive={false} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
