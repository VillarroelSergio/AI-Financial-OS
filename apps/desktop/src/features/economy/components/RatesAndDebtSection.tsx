import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { BondSnapshotMI, ForexSnapshotMI } from "@/lib/types/market-intelligence";

const CURVE_COLOR = "#2F8F6B";
const US_CURVE: Array<{ id: string; maturity: string }> = [
  { id: "us_2y", maturity: "2A" },
  { id: "us_5y", maturity: "5A" },
  { id: "us_10y", maturity: "10A" },
  { id: "us_30y", maturity: "30A" },
];

interface Props {
  bonds: BondSnapshotMI | null;
  forex: ForexSnapshotMI | null;
}

function Tile({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-xl border border-hairline-dark bg-surface-elevated p-4 flex flex-col gap-1" title={hint}>
      <span className="text-sm text-stone truncate">{label}</span>
      <span className="text-2xl font-semibold tabular-nums text-on-dark">{value}</span>
    </div>
  );
}

const fmtPct = (v: number | undefined | null, decimals = 2) =>
  v === undefined || v === null ? "—" : `${v.toLocaleString("es-ES", { minimumFractionDigits: decimals, maximumFractionDigits: decimals })} %`;

export default function RatesAndDebtSection({ bonds, forex }: Props) {
  const byId = new Map((bonds?.yields ?? []).map((b) => [b.catalog_item_id, b]));
  const curve = US_CURVE.map(({ id, maturity }) => ({
    maturity,
    yield: byId.get(id)?.yield_value ?? null,
  })).filter((p) => p.yield !== null);

  const spain = byId.get("spain_10y")?.yield_value ?? null;
  const bund = byId.get("germany_10y")?.yield_value ?? null;
  const premium = spain !== null && bund !== null ? (spain - bund) * 100 : null;
  const eurUsd = (forex?.rates ?? []).find((r) => r.catalog_item_id === "eur_usd")?.rate ?? null;

  const hasAnything = curve.length > 0 || spain !== null || eurUsd !== null;
  if (!hasAnything) return null;

  return (
    <section className="premium-card rounded-lg p-5 space-y-4">
      <h2 className="text-sm text-mute uppercase tracking-widest">Tipos y deuda</h2>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {curve.length >= 2 && (
          <div className="rounded-xl border border-hairline-dark bg-surface-elevated p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-caption text-stone">Curva de tipos EEUU</span>
              <span className="text-[10px] text-mute">{byId.get("us_10y")?.date ?? ""}</span>
            </div>
            <ResponsiveContainer width="100%" height={140}>
              <LineChart data={curve} margin={{ top: 8, right: 12, bottom: 0, left: -18 }}>
                <CartesianGrid strokeDasharray="2 4" stroke="rgba(255,255,255,0.06)" vertical={false} />
                <XAxis dataKey="maturity" tick={{ fill: "#a8adb3", fontSize: 11 }} axisLine={false} tickLine={false} />
                <YAxis
                  tick={{ fill: "#a8adb3", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  domain={["dataMin - 0.2", "dataMax + 0.2"]}
                  tickFormatter={(v: number) => v.toFixed(1)}
                />
                <Tooltip
                  cursor={{ stroke: "rgba(255,255,255,0.15)" }}
                  contentStyle={{ background: "#16181d", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, fontSize: 12 }}
                  labelStyle={{ color: "#a8adb3" }}
                  formatter={(value) => [fmtPct(Number(value)), "Rendimiento"]}
                />
                <Line
                  type="monotone"
                  dataKey="yield"
                  stroke={CURVE_COLOR}
                  strokeWidth={2}
                  dot={{ r: 4, fill: CURVE_COLOR, stroke: "#16181d", strokeWidth: 2 }}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
        <div className="grid grid-cols-2 gap-3 content-start">
          <Tile label="Bono España 10A" value={fmtPct(spain)} />
          <Tile label="Bund alemán 10A" value={fmtPct(bund)} />
          <Tile
            label="Prima de riesgo"
            value={premium === null ? "—" : `${premium.toFixed(0)} bps`}
            hint="Diferencial bono español 10A vs bund alemán"
          />
          <Tile
            label="EUR/USD"
            value={eurUsd === null ? "—" : eurUsd.toLocaleString("es-ES", { minimumFractionDigits: 4, maximumFractionDigits: 4 })}
          />
        </div>
      </div>
    </section>
  );
}
