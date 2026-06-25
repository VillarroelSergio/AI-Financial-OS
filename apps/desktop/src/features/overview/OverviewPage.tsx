import { ArrowLeftRight, Landmark, PiggyBank, TrendingUp, WalletCards } from "lucide-react";
import { ChartCard, EmptyState, KpiCard, LoadingState, PageHeader } from "@/components/ui/Dashboard";
import { useOverview } from "@/lib/hooks/useDashboard";
import { formatCurrency, formatPercent } from "@/lib/formatters/currency";

export default function OverviewPage() {
  const { data, loading } = useOverview();
  if (loading) return <LoadingState label="Calculando tu posición financiera" />;
  const d = data ?? { net_worth:"0", liquidity:"0", investments:"0", monthly_income:"0", monthly_expense:"0", monthly_savings:"0", savings_rate:0, currency:"EUR" };
  const savings = Number(d.monthly_savings);
  const allocation = [{name:"Liquidez",value:Number(d.liquidity),color:"#38bdf8"},{name:"Inversiones",value:Number(d.investments),color:"#5b5ef7"}];
  return <div className="p-8 max-w-[1500px] mx-auto space-y-6">
    <PageHeader eyebrow="Panel financiero" title="Resumen" description="Tu situación financiera actual" actions={<span className="text-xs text-stone">Actualizado hoy</span>}/>
    <div className="dashboard-grid">
      <div className="col-span-4"><KpiCard label="Patrimonio neto" value={formatCurrency(d.net_worth)} hint="Activos consolidados" icon={Landmark}/></div>
      <div className="col-span-4"><KpiCard label="Liquidez" value={formatCurrency(d.liquidity)} hint="Disponible en cuentas" icon={WalletCards}/></div>
      <div className="col-span-4"><KpiCard label="Inversiones" value={formatCurrency(d.investments)} hint="Valor de mercado" icon={TrendingUp}/></div>
      <div className="col-span-4"><KpiCard label="Ingresos del mes" value={formatCurrency(d.monthly_income)} hint="Periodo actual" icon={ArrowLeftRight}/></div>
      <div className="col-span-4"><KpiCard label="Gastos del mes" value={formatCurrency(d.monthly_expense)} hint="Periodo actual" positive={false} icon={ArrowLeftRight}/></div>
      <div className="col-span-4"><KpiCard label="Ahorro del mes" value={formatCurrency(d.monthly_savings)} delta={formatPercent(d.savings_rate)} hint="tasa de ahorro" positive={savings >= 0} icon={PiggyBank}/></div>
      <ChartCard className="col-span-8" title="Evolución del patrimonio" description="Histórico mensual consolidado">
        <EmptyState compact title="Aún no hay histórico suficiente" description="Necesitamos al menos dos cierres mensuales para mostrar una evolución fiable."/>
      </ChartCard>
      <ChartCard className="col-span-4" title="Distribución patrimonial" description="Composición actual">
        <div className="space-y-5">{allocation.map(x => <div key={x.name}><div className="flex justify-between gap-3 text-sm"><span className="text-stone">{x.name}</span><span className="financial-number text-on-dark">{formatCurrency(x.value)}</span></div><div className="mt-2 h-2 overflow-hidden rounded-full bg-white/5"><div className="h-full rounded-full" style={{width:`${Math.min(100,x.value/Math.max(1,Number(d.net_worth))*100)}%`,background:x.color}}/></div></div>)}</div>
      </ChartCard>
    </div>
  </div>;
}
