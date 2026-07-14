import { ArrowUpRight, BarChart2, ReceiptText, Target } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { PageHeader } from "@/components/ui/Dashboard";
import { useOverview } from "@/lib/hooks/useDashboard";
import { useHoldings, useInvestmentSummary } from "@/lib/hooks/useInvestments";
import { useTransactions } from "@/lib/hooks/useTransactions";
import { useGoals } from "@/lib/hooks/useGoals";
import { useInsights } from "@/features/insights/hooks/useInsights";
import { formatCurrency, formatPercent } from "@/lib/formatters/currency";
import BalanceGeneralPanel from "./components/BalanceGeneralPanel";

function CardSkeleton({ rows = 3 }: { rows?: number }) {
  return (
    <div className="animate-pulse space-y-2 py-2">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-4 rounded bg-surface-elevated" />
      ))}
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="p-8 max-w-[1500px] mx-auto space-y-6" aria-label="Preparando resumen">
      <div className="animate-pulse space-y-5 py-2">
        <div className="h-16 w-64 rounded-lg bg-surface-elevated" />
        <div className="h-5 w-[420px] max-w-full rounded bg-surface-elevated" />
      </div>
      <div className="grid gap-4 lg:grid-cols-3 animate-pulse">
        {Array.from({ length: 3 }).map((_, index) => <div key={index} className="premium-card h-28 rounded-lg" />)}
      </div>
      <div className="grid gap-6 lg:grid-cols-[2fr_1fr] animate-pulse">
        <div className="premium-card h-72 rounded-lg" />
        <div className="space-y-6"><div className="premium-card h-32 rounded-lg" /><div className="premium-card h-32 rounded-lg" /></div>
      </div>
    </div>
  );
}

function SectionCard({ title, more, children }: { title: string; more: string; children: React.ReactNode }) {
  return (
    <div className="premium-card rounded-lg p-5">
      <div className="mb-3 flex items-center justify-between">
        <p className="font-semibold">{title}</p>
        <Link to={more} className="flex items-center gap-1 text-xs text-primary-bright hover:underline">
          Ver más <ArrowUpRight size={12} />
        </Link>
      </div>
      {children}
    </div>
  );
}

export default function DashboardPage() {
  const navigate = useNavigate();
  const { data: overview, loading } = useOverview();
  const { holdings, loading: holdingsLoading } = useHoldings();
  const { summary } = useInvestmentSummary();
  const { transactions, loading: txLoading } = useTransactions({ limit: 5 });
  const { goals, loading: goalsLoading } = useGoals();
  const { data: insightsData, loading: insightsLoading } = useInsights();

  if (loading) return <DashboardSkeleton />;

  const activeInvestments = holdings.filter((h) => !h.is_mock).length;
  const returnPct = summary?.return_percent ?? 0;
  const recent = transactions;
  const insights = (insightsData?.insights ?? []).slice(0, 2);

  return (
    <div className="p-8 max-w-[1500px] mx-auto space-y-6">
      <PageHeader
        title="Resumen"
        description="Monitorea tus finanzas, inversiones y gastos."
      />

      <section>
        <div className="mb-3 flex items-center justify-between"><div><p className="text-sm font-semibold text-on-dark">Señales del mes</p><p className="mt-1 text-xs text-stone">Lo importante antes del detalle.</p></div><Link to="/finances?tab=gastos" className="text-xs text-primary-bright hover:underline">Ver gastos</Link></div>
        <div className="grid gap-4 lg:grid-cols-3">
          <button type="button" onClick={() => navigate("/finances?tab=cuentas")} className="premium-card ui-pressable rounded-lg p-5 text-left transition-colors hover:border-[var(--border-strong)]"><p className="text-xs text-stone">Patrimonio neto</p><p className="financial-number mt-2 text-xl font-semibold">{formatCurrency(overview?.net_worth ?? "0")}</p><p className="mt-2 text-xs text-primary-bright">Revisar cuentas</p></button>
          <button type="button" onClick={() => navigate("/finances?tab=gastos")} className="premium-card ui-pressable rounded-lg p-5 text-left transition-colors hover:border-[var(--border-strong)]"><p className="text-xs text-stone">Ahorro neto</p><p className={`financial-number mt-2 text-xl font-semibold ${Number(overview?.monthly_savings ?? 0) >= 0 ? "text-accent-teal" : "text-accent-danger"}`}>{formatCurrency(overview?.monthly_savings ?? "0")}</p><p className="mt-2 text-xs text-primary-bright">Analizar gastos</p></button>
          <button type="button" onClick={() => navigate("/finances?tab=gastos")} className="premium-card ui-pressable rounded-lg p-5 text-left transition-colors hover:border-[var(--border-strong)]"><p className="text-xs text-stone">Ritmo de gasto</p><p className="financial-number mt-2 text-xl font-semibold">{formatCurrency(overview?.monthly_expense ?? "0")}</p><p className="mt-1 text-xs text-stone">{formatPercent(overview?.savings_rate ?? 0)} de ahorro · <span className="text-primary-bright">Ver gastos</span></p></button>
        </div>
      </section>

      <div className="dashboard-grid">
        <div className="col-span-8 space-y-6">
          <SectionCard title="Últimos movimientos" more="/finances?tab=movimientos">
            {txLoading ? <CardSkeleton rows={5} /> : recent.length === 0 ? (
              <div className="py-8 text-center">
                <ReceiptText className="mx-auto mb-3 text-stone" />
                <p className="font-semibold">No tienes movimientos recientes</p>
                <p className="mt-1 text-sm text-stone">Importa el extracto de tu banco para ver tus transacciones aquí.</p>
                <button onClick={() => navigate("/finances?tab=importar")} className="mercury-button-primary mt-4 rounded-lg px-4 py-2 text-sm">Añade tus movimientos</button>
              </div>
            ) : (
              <div>
                {recent.map((t) => (
                  <div key={t.id} className="flex items-center justify-between border-t border-divider-soft py-2.5 text-sm first:border-0">
                    <span className="truncate pr-4">{t.description}<span className="ml-2 text-xs text-stone">{t.date}</span></span>
                    <span className={`financial-number shrink-0 ${Number(t.amount) < 0 ? "text-accent-danger" : "text-accent-teal"}`}>
                      {formatCurrency(t.amount)}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </SectionCard>

          <SectionCard title="Portafolio de inversiones" more="/investments">
            {holdingsLoading ? <CardSkeleton rows={3} /> : activeInvestments === 0 ? (
              <div className="py-8 text-center">
                <BarChart2 className="mx-auto mb-3 text-stone" />
                <p className="font-semibold">Aún no tienes inversiones</p>
                <p className="mt-1 text-sm text-stone">Da de alta tus acciones y fondos para ver tu portafolio aquí.</p>
                <button onClick={() => navigate("/investments")} className="mercury-button-primary mt-4 rounded-lg px-4 py-2 text-sm">Añadir inversión</button>
              </div>
            ) : (
              <div className="grid grid-cols-3 gap-4">
                <div><p className="text-xs text-stone">Valor total</p><p className="financial-number mt-1 text-lg font-semibold">{formatCurrency(summary?.total_value ?? "0")}</p></div>
                <div><p className="text-xs text-stone">Aportado</p><p className="financial-number mt-1 text-lg font-semibold">{formatCurrency(summary?.total_invested ?? "0")}</p></div>
                <div><p className="text-xs text-stone">Retorno</p><p className={`financial-number mt-1 text-lg font-semibold ${returnPct >= 0 ? "text-accent-teal" : "text-accent-danger"}`}>{returnPct >= 0 ? "+" : ""}{returnPct.toFixed(1)}%</p></div>
              </div>
            )}
          </SectionCard>
        </div>

        <div className="col-span-4 space-y-6">
          <SectionCard title="Objetivos" more="/goals">
            <button onClick={() => navigate("/goals")} className="flex w-full items-center gap-2 rounded-lg border border-dashed border-hairline-dark px-3 py-2.5 text-sm text-stone hover:border-primary hover:text-on-dark">
              <Target size={14} /> Nuevo objetivo
            </button>
            {goalsLoading && <CardSkeleton rows={2} />}
            {!goalsLoading && goals.slice(0, 2).map((g) => (
              <div key={g.id} className="mt-2 rounded-lg border border-hairline-dark bg-black/20 px-3 py-2.5">
                <p className="text-sm font-medium">{g.name}</p>
                <p className="mt-0.5 text-xs text-stone">
                  {formatCurrency(g.current_amount)} de {formatCurrency(g.target_amount)}
                </p>
              </div>
            ))}
          </SectionCard>

          <SectionCard title="Insights" more="/insights">
            {insightsLoading ? <CardSkeleton rows={2} /> : insights.length === 0 ? (
              <p className="py-4 text-sm text-stone">Cuando haya suficientes datos verás aquí recomendaciones basadas en tus finanzas.</p>
            ) : (
              insights.map((i) => (
                <div key={i.id} className={`mt-2 rounded-lg border px-3 py-2.5 first:mt-0 ${i.severity === "warning" || i.severity === "critical" ? "border-accent-warning/30 bg-accent-warning/5" : "border-accent-teal/30 bg-accent-teal/5"}`}>
                  <p className="text-sm font-medium">{i.title}</p>
                  <p className="mt-0.5 text-xs text-stone">{i.summary}</p>
                </div>
              ))
            )}
          </SectionCard>
        </div>
      </div>

      <BalanceGeneralPanel />
    </div>
  );
}
