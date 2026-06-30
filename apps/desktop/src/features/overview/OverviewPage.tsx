import { AlertTriangle, ArrowLeftRight, Landmark, PiggyBank, ShieldCheck, TrendingDown, TrendingUp, WalletCards } from "lucide-react";
import { ChartCard, EmptyState, KpiCard, LoadingState, PageHeader } from "@/components/ui/Dashboard";
import { useOverview } from "@/lib/hooks/useDashboard";
import { formatCurrency, formatPercent } from "@/lib/formatters/currency";
import { useInsights } from "@/features/insights/hooks/useInsights";
import { InsightCard } from "@/features/insights/components/InsightCard";

export default function OverviewPage() {
  const { data, loading } = useOverview();
  const { data: insightsData } = useInsights({ limit: 2 }, []);
  const topInsights = insightsData?.insights ?? [];
  if (loading) return <LoadingState label="Calculando tu posicion financiera" />;

  const d = data ?? { net_worth: "0", liquidity: "0", investments: "0", monthly_income: "0", monthly_expense: "0", monthly_savings: "0", savings_rate: 0, currency: "EUR" };
  const netWorth = Number(d.net_worth);
  const savings = Number(d.monthly_savings);
  const debt = 0;
  const allocation = [
    { name: "Liquidez", value: Number(d.liquidity), color: "#38bdf8" },
    { name: "Inversiones", value: Number(d.investments), color: "#5b5ef7" },
    { name: "Deuda", value: debt, color: "#ff4d63" },
  ];

  return (
    <div className="p-8 max-w-[1500px] mx-auto space-y-6">
      <PageHeader eyebrow="Panel financiero" title="Resumen" description="Vision ejecutiva de patrimonio, liquidez, flujo mensual y proximas acciones." actions={<span className="text-xs text-stone">Actualizado hoy</span>} />

      <section className="premium-card rounded-lg overflow-hidden">
        <div className="grid gap-6 p-6 lg:grid-cols-[1.2fr_.8fr]">
          <div>
            <p className="text-[11px] font-semibold uppercase tracking-[.18em] text-primary-bright">Posicion consolidada</p>
            <h2 className="financial-number mt-4 text-[46px] leading-none font-semibold text-on-dark">{formatCurrency(d.net_worth)}</h2>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-stone">Vista de control para patrimonio, liquidez y capacidad de ahorro con senales accionables sin ruido operativo.</p>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg border border-hairline-dark bg-white/[.035] p-4">
              <p className="text-xs text-stone">Liquidez</p>
              <p className="financial-number mt-2 text-xl font-semibold text-on-dark">{formatCurrency(d.liquidity)}</p>
            </div>
            <div className="rounded-lg border border-hairline-dark bg-white/[.035] p-4">
              <p className="text-xs text-stone">Ahorro mensual</p>
              <p className={`financial-number mt-2 text-xl font-semibold ${savings >= 0 ? "text-accent-teal" : "text-accent-danger"}`}>{formatCurrency(savings)}</p>
            </div>
            <div className="col-span-2 rounded-lg border border-hairline-dark bg-white/[.035] p-4">
              <div className="flex items-center justify-between text-xs text-stone">
                <span>Tasa de ahorro</span>
                <span className="text-on-dark">{formatPercent(d.savings_rate)}</span>
              </div>
              <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/[.06]">
                <div className="h-full rounded-full bg-accent-teal" style={{ width: `${Math.max(0, Math.min(100, d.savings_rate * 100))}%` }} />
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="dashboard-grid">
        <div className="col-span-3"><KpiCard label="Patrimonio neto" value={formatCurrency(d.net_worth)} hint="Activos consolidados" icon={Landmark} /></div>
        <div className="col-span-3"><KpiCard label="Liquidez" value={formatCurrency(d.liquidity)} hint="Disponible en cuentas" icon={WalletCards} /></div>
        <div className="col-span-3"><KpiCard label="Inversiones" value={formatCurrency(d.investments)} hint="Valor de mercado" icon={TrendingUp} /></div>
        <div className="col-span-3"><KpiCard label="Deuda" value={formatCurrency(debt)} hint="Sin deuda registrada" positive={false} icon={TrendingDown} /></div>
        <div className="col-span-3"><KpiCard label="Ingresos del mes" value={formatCurrency(d.monthly_income)} hint="Periodo actual" icon={ArrowLeftRight} /></div>
        <div className="col-span-3"><KpiCard label="Gastos del mes" value={formatCurrency(d.monthly_expense)} hint="Periodo actual" positive={false} icon={ArrowLeftRight} /></div>
        <div className="col-span-3"><KpiCard label="Ahorro neto" value={formatCurrency(d.monthly_savings)} delta={formatPercent(d.savings_rate)} hint="tasa de ahorro" positive={savings >= 0} icon={PiggyBank} /></div>
        <div className="col-span-3"><KpiCard label="Rentabilidad cartera" value="Sin dato" hint="Requiere precios de inversiones" icon={TrendingUp} /></div>

        <ChartCard className="col-span-4" title="Salud financiera" description="Lectura rapida">
          <div className="space-y-4">
            <div className="rounded-xl bg-accent-teal/10 p-4">
              <p className="text-xs text-accent-teal">Tasa de ahorro</p>
              <p className="mt-2 text-lg font-semibold text-on-dark">{savings >= 0 ? "Positiva" : "Negativa"}</p>
              <p className="mt-1 text-sm text-stone">Tu ahorro neto del mes es {formatCurrency(savings)}.</p>
            </div>
            <div className="rounded-xl bg-white/5 p-4">
              <p className="text-xs text-stone">Cambio patrimonio vs mes anterior</p>
              <p className="mt-2 font-semibold text-on-dark">Sin historico suficiente</p>
            </div>
          </div>
        </ChartCard>

        <ChartCard className="col-span-4" title="Patrimonio" description="Composicion actual">
          <div className="space-y-5">
            {allocation.map((x) => (
              <div key={x.name}>
                <div className="flex justify-between gap-3 text-sm">
                  <span className="text-stone">{x.name}</span>
                  <span className="financial-number text-on-dark">{formatCurrency(x.value)}</span>
                </div>
                <div className="mt-2 h-2 overflow-hidden rounded-full bg-white/5">
                  <div className="h-full rounded-full" style={{ width: `${Math.min(100, x.value / Math.max(1, netWorth) * 100)}%`, background: x.color }} />
                </div>
              </div>
            ))}
          </div>
        </ChartCard>

        <ChartCard className="col-span-4" title="Proximas acciones" description="Insights no agresivos">
          <div className="space-y-3">
            <div className="flex gap-3 rounded-xl bg-white/5 p-4"><ShieldCheck className="mt-0.5 text-accent-teal" size={18} /><p className="text-sm text-stone">Revisa que las cuentas incluidas en patrimonio esten actualizadas.</p></div>
            <div className="flex gap-3 rounded-xl bg-white/5 p-4"><AlertTriangle className="mt-0.5 text-amber-300" size={18} /><p className="text-sm text-stone">Hay datos de mercado limitados; no se calcula impacto sobre cartera.</p></div>
          </div>
        </ChartCard>

        <ChartCard className="col-span-6" title="Flujo mensual" description="Ingresos, gastos y ahorro neto">
          <div className="grid grid-cols-3 gap-4">
            <div className="rounded-xl bg-white/5 p-4"><p className="text-xs text-stone">Ingresos</p><p className="financial-number mt-2 text-on-dark">{formatCurrency(d.monthly_income)}</p></div>
            <div className="rounded-xl bg-white/5 p-4"><p className="text-xs text-stone">Gastos</p><p className="financial-number mt-2 text-on-dark">{formatCurrency(d.monthly_expense)}</p></div>
            <div className="rounded-xl bg-white/5 p-4"><p className="text-xs text-stone">Ahorro</p><p className="financial-number mt-2 text-on-dark">{formatCurrency(d.monthly_savings)}</p></div>
          </div>
        </ChartCard>

        <ChartCard className="col-span-6" title="Gastos principales" description="Pendiente de categorias del periodo">
          <EmptyState compact title="Sin desglose en resumen" description="Abre Gastos para ver categoria principal, porcentajes y filtros por periodo." />
        </ChartCard>

        {topInsights.length > 0 && (
          <ChartCard className="col-span-12" title="Top Insights" description="Señales prioritarias detectadas en tus finanzas" action={<a href="/insights" className="text-xs text-primary-bright hover:underline">Ver todos</a>}>
            <div className="space-y-3">
              {topInsights.map((i) => <InsightCard key={i.id} insight={i} compact />)}
            </div>
          </ChartCard>
        )}
      </div>
    </div>
  );
}
