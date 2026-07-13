import { ArrowUpRight, BarChart2, PiggyBank, ReceiptText, Target, TrendingDown } from "lucide-react";
import { motion } from "framer-motion";
import { Link, useNavigate } from "react-router-dom";
import { KpiCard, PageHeader } from "@/components/ui/Dashboard";
import { CardSkeleton, DashboardSkeleton } from "@/components/ui/Skeleton";
import { staggerContainer, staggerItem } from "@/components/ui/motion";
import { useOverview, useSpendingMonthly } from "@/lib/hooks/useDashboard";
import { useHoldings, useInvestmentSummary } from "@/lib/hooks/useInvestments";
import { useTransactions } from "@/lib/hooks/useTransactions";
import { useGoals } from "@/lib/hooks/useGoals";
import { useInsights } from "@/features/insights/hooks/useInsights";
import { formatCurrency, formatPercent } from "@/lib/formatters/currency";
import BalanceGeneralPanel from "./components/BalanceGeneralPanel";
import NetWorthHero from "./components/NetWorthHero";
import InsightStrip from "./components/InsightStrip";

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
  const { data: insightsData } = useInsights();
  const monthly = useSpendingMonthly(6);

  if (loading) return <DashboardSkeleton />;

  const activeInvestments = holdings.filter((h) => !h.is_mock).length;
  const returnPct = summary?.return_percent ?? 0;
  const recent = transactions;
  const insights = (insightsData?.insights ?? []).slice(0, 2);

  // Delta de gastos vs media de meses anteriores (solo si hay histórico; nunca inventado)
  let expenseDelta: string | undefined;
  let expenseIsGood = true;
  if (monthly.length >= 2) {
    const current = Number(monthly[monthly.length - 1].expense);
    const prev = monthly.slice(0, -1).map((m) => Number(m.expense));
    const avg = prev.reduce((a, b) => a + b, 0) / prev.length;
    if (avg > 0) {
      const pct = ((current - avg) / avg) * 100;
      expenseIsGood = current <= avg;
      expenseDelta = `${pct >= 0 ? "+" : ""}${pct.toFixed(0)}%`;
    }
  }
  const savingsRate = overview?.savings_rate ?? 0;

  return (
    <div className="p-8 max-w-[1500px] mx-auto space-y-6">
      <PageHeader title="Resumen" description="Cómo van tus finanzas, inversiones y gastos." />

      <NetWorthHero netWorth={overview?.net_worth ?? "0"} />

      <motion.div className="dashboard-grid" variants={staggerContainer} initial="hidden" animate="show">
        <motion.div className="col-span-4" variants={staggerItem}>
          <KpiCard
            label="Gastos del mes"
            value={formatCurrency(overview?.monthly_expense ?? "0")}
            icon={TrendingDown}
            delta={expenseDelta}
            positive={expenseIsGood}
            hint={expenseDelta ? "vs media" : "Mes en curso"}
          />
        </motion.div>
        <motion.div className="col-span-4" variants={staggerItem}>
          <KpiCard
            label="Ahorro neto"
            value={formatCurrency(overview?.monthly_savings ?? "0")}
            icon={PiggyBank}
            hint={`Tasa de ahorro ${formatPercent(savingsRate)}`}
          />
        </motion.div>
        <motion.div className="col-span-4" variants={staggerItem}>
          <KpiCard
            label="Inversiones"
            value={`${activeInvestments} ${activeInvestments === 1 ? "posición" : "posiciones"}`}
            icon={BarChart2}
            delta={activeInvestments > 0 ? `${returnPct >= 0 ? "+" : ""}${returnPct.toFixed(1)}%` : undefined}
            positive={returnPct >= 0}
            hint={activeInvestments > 0 ? "rentabilidad" : "Sin posiciones"}
          />
        </motion.div>
      </motion.div>

      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <p className="font-semibold text-[var(--text-primary)]">Insights</p>
          <Link to="/insights" className="flex items-center gap-1 text-xs text-primary-bright hover:underline">
            Ver todos <ArrowUpRight size={12} />
          </Link>
        </div>
        {insights.length > 0 ? (
          <InsightStrip insights={insights} />
        ) : (
          <p className="text-sm text-stone">Aún no hay insights destacados. Ábrelos para explorar patrones y alertas de tus finanzas.</p>
        )}
      </section>

      <BalanceGeneralPanel />

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
              <div key={g.id} className="mt-2 rounded-lg border border-hairline-dark bg-[var(--bg-card-elevated)] px-3 py-2.5">
                <p className="text-sm font-medium">{g.name}</p>
                <p className="mt-0.5 text-xs text-stone">
                  {formatCurrency(g.current_amount)} de {formatCurrency(g.target_amount)}
                </p>
              </div>
            ))}
          </SectionCard>
        </div>
      </div>
    </div>
  );
}
