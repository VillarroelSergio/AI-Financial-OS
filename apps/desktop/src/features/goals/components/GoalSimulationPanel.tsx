import { useState, useEffect, useCallback } from "react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine,
} from "recharts";
import { TrendingUp, RefreshCw, ChevronDown, ChevronUp } from "lucide-react";
import { simulateGoal } from "@/lib/api/goals";
import type { SimulationResult, ScenarioProjection } from "@/lib/api/goals";
import { formatCurrency } from "@/lib/formatters/currency";

// ── Helpers ───────────────────────────────────────────────────────────────────

function monthsToHuman(months: number | null): string {
  if (months === null) return "No alcanzable en 30 años";
  if (months === 0) return "Ya alcanzado";
  const y = Math.floor(months / 12);
  const m = months % 12;
  const parts: string[] = [];
  if (y > 0) parts.push(`${y} año${y > 1 ? "s" : ""}`);
  if (m > 0) parts.push(`${m} mes${m > 1 ? "es" : ""}`);
  return parts.join(" y ");
}

function fmtDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(`${iso}T00:00:00`).toLocaleDateString("es-ES", {
    month: "long", year: "numeric",
  });
}

function fmtPct(r: number) {
  return `${(r * 100).toFixed(0)} %`;
}

// ── Scenario card ─────────────────────────────────────────────────────────────

function ScenarioCard({ sc }: { sc: ScenarioProjection }) {
  const reachable = sc.months_to_target !== null;
  return (
    <div className="rounded-xl border border-hairline-dark bg-surface-deep px-4 py-3 space-y-1">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium" style={{ color: sc.color }}>
          {sc.label}
        </span>
        <span className="text-[10px] text-mute">{fmtPct(sc.annual_growth_rate)} / año</span>
      </div>
      <p className="text-sm font-semibold text-on-dark">
        {reachable ? fmtDate(sc.projected_date) : "No alcanzable"}
      </p>
      <p className="text-[11px] text-stone">
        {reachable ? monthsToHuman(sc.months_to_target) : "En 30 años no se alcanza el objetivo"}
      </p>
      {sc.achievable_by_target_date !== null && (
        <span className={`inline-block mt-0.5 text-[10px] font-medium px-1.5 py-0.5 rounded-full
          ${sc.achievable_by_target_date
            ? "bg-emerald-500/15 text-emerald-400"
            : "bg-red-500/15 text-red-400"}`}>
          {sc.achievable_by_target_date ? "En plazo" : "Fuera de plazo"}
        </span>
      )}
    </div>
  );
}

// ── Custom tooltip ────────────────────────────────────────────────────────────

function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border border-hairline-dark bg-surface-deep px-3 py-2 text-xs space-y-1 shadow-xl">
      <p className="text-mute mb-1">{label}</p>
      {payload.map((p: any) => (
        <p key={p.dataKey} style={{ color: p.color }}>
          {p.name}: {formatCurrency(p.value)}
        </p>
      ))}
    </div>
  );
}

// ── Main panel ────────────────────────────────────────────────────────────────

interface Props {
  goalId: string;
  targetAmount: string;
  hasContribution: boolean;
}

export default function GoalSimulationPanel({ goalId, targetAmount, hasContribution }: Props) {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SimulationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [inflationRate, setInflationRate] = useState(3);

  const run = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await simulateGoal(goalId, { inflation_rate: inflationRate / 100 });
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al calcular la simulación.");
    } finally {
      setLoading(false);
    }
  }, [goalId, inflationRate]);

  useEffect(() => {
    if (open && !result) run();
  }, [open, result, run]);

  // Reduce chart data density for readability
  const chartData = result
    ? result.monthly_data.filter((_, i) => i % 3 === 0 || i === result.monthly_data.length - 1)
    : [];

  const target = parseFloat(targetAmount);

  return (
    <div className="border-t border-hairline-dark">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-5 py-3 text-xs text-stone hover:text-on-dark transition-colors"
      >
        <span className="flex items-center gap-1.5">
          <TrendingUp size={12} />
          Proyección y escenarios
        </span>
        {open ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>

      {open && (
        <div className="px-5 pb-5 space-y-4">
          {/* Inflation control */}
          <div className="flex items-center gap-3">
            <label className="text-xs text-mute whitespace-nowrap">
              Inflación anual:
            </label>
            <input
              type="range" min={0} max={10} step={0.5}
              value={inflationRate}
              onChange={(e) => setInflationRate(Number(e.target.value))}
              onMouseUp={run}
              onTouchEnd={run}
              className="flex-1 accent-primary h-1"
            />
            <span className="text-xs font-mono text-on-dark w-10 text-right">
              {inflationRate.toFixed(1)} %
            </span>
          </div>

          {loading && (
            <div className="flex items-center gap-2 text-xs text-mute py-4">
              <RefreshCw size={12} className="animate-spin" />
              Calculando...
            </div>
          )}

          {error && (
            <p className="text-xs text-red-400">{error}</p>
          )}

          {result && !loading && (
            <>
              {/* Inflation note */}
              {result.inflation_adjusted_target > target && (
                <p className="text-[11px] text-amber-400/70 leading-snug">
                  Con una inflación del {(result.inflation_rate * 100).toFixed(1)} %/año,
                  necesitarás <strong>{formatCurrency(result.inflation_adjusted_target)}</strong> en
                  el futuro para mantener el poder adquisitivo equivalente
                  a {formatCurrency(target)} hoy.
                </p>
              )}

              {!hasContribution && (
                <p className="text-[11px] text-stone">
                  Sin aportación mensual configurada — la proyección muestra solo el crecimiento del capital actual.
                </p>
              )}

              {/* Scenario cards */}
              <div className="grid grid-cols-3 gap-2">
                {result.scenarios.map((sc) => (
                  <ScenarioCard key={sc.scenario} sc={sc} />
                ))}
              </div>

              {/* Chart */}
              <div className="h-40">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: 0 }}>
                    <defs>
                      <linearGradient id={`gc-${goalId}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#94a3b8" stopOpacity={0.15} />
                        <stop offset="95%" stopColor="#94a3b8" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id={`gb-${goalId}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.2} />
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id={`go-${goalId}`} x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.15} />
                        <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis
                      dataKey="label"
                      tick={{ fill: "#6b7280", fontSize: 9 }}
                      interval="preserveStartEnd"
                      tickLine={false}
                      axisLine={false}
                    />
                    <YAxis hide domain={[0, "auto"]} />
                    <Tooltip content={<ChartTooltip />} />
                    <ReferenceLine
                      y={target}
                      stroke="#10b981"
                      strokeDasharray="4 2"
                      strokeOpacity={0.5}
                    />
                    <Area
                      type="monotone"
                      dataKey="conservative"
                      name="Conservador"
                      stroke="#94a3b8"
                      strokeWidth={1.5}
                      fill={`url(#gc-${goalId})`}
                      dot={false}
                    />
                    <Area
                      type="monotone"
                      dataKey="base"
                      name="Base"
                      stroke="#10b981"
                      strokeWidth={1.5}
                      fill={`url(#gb-${goalId})`}
                      dot={false}
                    />
                    <Area
                      type="monotone"
                      dataKey="optimistic"
                      name="Optimista"
                      stroke="#f59e0b"
                      strokeWidth={1.5}
                      fill={`url(#go-${goalId})`}
                      dot={false}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Aportación necesaria si no llega a plazo */}
              {result.monthly_contribution_needed != null && result.monthly_contribution_needed > result.monthly_contribution && (
                <div className="rounded-xl bg-amber-500/10 border border-amber-500/20 p-3 space-y-0.5">
                  <p className="text-xs text-stone">Para llegar en plazo (escenario base) necesitarías aportar</p>
                  <p className="text-lg font-semibold text-on-dark">
                    {result.monthly_contribution_needed.toLocaleString("es-ES", { style: "currency", currency: "EUR" })} / mes
                  </p>
                </div>
              )}

              <p className="text-[10px] text-mute">
                Proyección orientativa. Escenarios basados en rentabilidades históricas.
                No constituye asesoramiento financiero.
              </p>
            </>
          )}
        </div>
      )}
    </div>
  );
}
