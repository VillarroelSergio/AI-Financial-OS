import { useMemo } from "react";
import { Area, AreaChart, ResponsiveContainer } from "recharts";
import { formatCurrency } from "@/lib/formatters/currency";
import { CountUp } from "@/components/ui/motion";
import { useBalanceSheet, useSnapshots } from "@/lib/hooks/useNetWorth";

function monthLabel(): string {
  const s = new Intl.DateTimeFormat("es-ES", { month: "long", year: "numeric" }).format(new Date());
  return s.charAt(0).toUpperCase() + s.slice(1);
}

// dot solo en el punto final del sparkline
function LastDot(props: { cx?: number; cy?: number; index?: number; dataLength: number }) {
  const { cx, cy, index, dataLength } = props;
  if (cx == null || cy == null || index !== dataLength - 1) return <circle r={0} />;
  return <circle cx={cx} cy={cy} r={3} fill="#6EE7B7" />;
}

export default function NetWorthHero({ netWorth }: { netWorth: string }) {
  const { data: snapshots } = useSnapshots();
  const { data: balance } = useBalanceSheet();

  const series = useMemo(
    () =>
      (snapshots ?? [])
        .slice()
        .sort((a, b) => a.month.localeCompare(b.month))
        .slice(-6)
        .map((s) => ({ month: s.month, value: Number(s.net_worth) })),
    [snapshots],
  );

  const change = balance?.net_worth_change != null ? Number(balance.net_worth_change) : null;
  const noLiabilities = balance ? Number(balance.total_liabilities) === 0 : false;
  const showSpark = series.length >= 2;

  return (
    <section
      className="relative overflow-hidden rounded-[20px] p-6 sm:p-7"
      style={{ background: "linear-gradient(160deg, var(--bg-hero-from), var(--bg-hero-to))", boxShadow: "var(--shadow-hero)" }}
    >
      <div className="flex items-end justify-between gap-6">
        <div className="min-w-0">
          <p className="text-[11px] uppercase tracking-wide" style={{ color: "var(--text-on-hero-secondary)" }}>
            Patrimonio neto · {monthLabel()}
          </p>
          <CountUp
            value={Number(netWorth)}
            format={formatCurrency}
            className="financial-number mt-2 block leading-none"
            style={{ color: "var(--text-on-hero)", fontSize: "var(--text-hero-value)", fontWeight: 700, letterSpacing: "-1px" }}
          />
          {change != null && (
            <p className="mt-2 text-[13px]" style={{ color: change >= 0 ? "var(--positive-on-hero)" : "var(--negative-on-hero)" }}>
              {change >= 0 ? "▲ +" : "▼ -"}
              {formatCurrency(Math.abs(change))} este mes
              {noLiabilities ? " · sin pasivos" : ""}
            </p>
          )}
        </div>

        {showSpark && (
          <div className="hidden h-16 w-44 shrink-0 sm:block">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={series} margin={{ top: 6, bottom: 6, left: 0, right: 4 }}>
                <defs>
                  <linearGradient id="nwHeroFill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#6EE7B7" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="#6EE7B7" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <Area
                  type="monotone"
                  dataKey="value"
                  stroke="#6EE7B7"
                  strokeWidth={2}
                  fill="url(#nwHeroFill)"
                  dot={(p) => <LastDot key={`d-${p.index}`} cx={p.cx} cy={p.cy} index={p.index} dataLength={series.length} />}
                  isAnimationActive={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </section>
  );
}
