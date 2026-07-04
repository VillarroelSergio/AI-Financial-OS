import { ArrowUpRight, BarChart2, ReceiptText, Target, TrendingDown, TrendingUp, Wallet } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { KpiCard, LoadingState, PageHeader } from "@/components/ui/Dashboard";
import { useOverview } from "@/lib/hooks/useDashboard";
import { useHoldings, useInvestmentSummary } from "@/lib/hooks/useInvestments";
import { useTransactions } from "@/lib/hooks/useTransactions";
import { useGoals } from "@/lib/hooks/useGoals";
import { useInsights } from "@/features/insights/hooks/useInsights";
import { formatCurrency } from "@/lib/formatters/currency";

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
  const { holdings } = useHoldings();
  const { summary } = useInvestmentSummary();
  const { transactions } = useTransactions();
  const { goals } = useGoals();
  const { data: insightsData } = useInsights();

  if (loading) return <LoadingState label="Cargando tu resumen" />;

  const activeInvestments = holdings.filter((h) => !h.is_mock).length;
  const returnPct = summary?.return_percent ?? 0;
  const recent = transactions.slice(0, 5);
  const insights = (insightsData?.insights ?? []).slice(0, 2);

  return (
    <div className="p-8 max-w-[1500px] mx-auto space-y-6">
      <PageHeader
        eyebrow="Private command center"
        title="Dashboard"
        description="Monitorea tus finanzas, inversiones y gastos."
      />

      <div className="dashboard-grid">
        <div className="col-span-3"><KpiCard label="Balance total" value={formatCurrency(overview?.net_worth ?? "0")} hint="Patrimonio neto" icon={Wallet} /></div>
        <div className="col-span-3"><KpiCard label="Gastos del mes" value={formatCurrency(overview?.monthly_expense ?? "0")} hint="Mes en curso" icon={TrendingDown} positive={false} /></div>
        <div className="col-span-3"><KpiCard label="Inversiones activas" value={String(activeInvestments)} hint="Posiciones reales" icon={BarChart2} /></div>
        <div className="col-span-3"><KpiCard label="Rendimiento" value={`${returnPct >= 0 ? "+" : ""}${returnPct.toFixed(1)}%`} hint="Cartera de inversión" icon={TrendingUp} positive={returnPct >= 0} /></div>
      </div>

      <div className="dashboard-grid">
        <div className="col-span-8 space-y-6">
          <SectionCard title="Últimos movimientos" more="/finances?tab=movimientos">
            {recent.length === 0 ? (
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
            {activeInvestments === 0 ? (
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
            {goals.slice(0, 2).map((g) => (
              <div key={g.id} className="mt-2 rounded-lg border border-hairline-dark bg-black/20 px-3 py-2.5">
                <p className="text-sm font-medium">{g.name}</p>
                <p className="mt-0.5 text-xs text-stone">
                  {formatCurrency(g.current_amount)} de {formatCurrency(g.target_amount)}
                </p>
              </div>
            ))}
          </SectionCard>

          <SectionCard title="Insights" more="/insights">
            {insights.length === 0 ? (
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
    </div>
  );
}
