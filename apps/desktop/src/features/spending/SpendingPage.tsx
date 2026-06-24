import { useState } from "react";
import { ChevronLeft, ChevronRight, ReceiptText, TrendingDown, TrendingUp, Wallet } from "lucide-react";
import { ChartCard, EmptyState, KpiCard, LoadingState, PageHeader } from "@/components/ui/Dashboard";
import { useSpending } from "@/lib/hooks/useDashboard";
import { formatCurrency, formatPercent } from "@/lib/formatters/currency";

const COLORS=["#5b5ef7","#00c896","#f59e0b","#ff4d63","#38bdf8","#a78bfa"];
const currentMonth=()=>{const d=new Date();return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}`};
const moveMonth=(value:string,delta:number)=>{const [y,m]=value.split("-").map(Number);const d=new Date(y,m-1+delta,1);return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}`};

export default function SpendingPage(){
  const [month,setMonth]=useState(currentMonth); const {data,loading}=useSpending(month);
  if(loading)return <LoadingState label="Analizando el mes"/>;
  const expense=Number(data?.total_expense??0), income=Number(data?.total_income??0), rate=income?Math.max(0,(income-expense)/income):0;
  return <div className="p-8 max-w-[1500px] mx-auto space-y-6">
    <PageHeader eyebrow="Flujo mensual" title="Gastos" description="Entiende dónde va tu dinero y cómo evoluciona tu ahorro" actions={<div className="flex items-center rounded-xl border border-hairline-dark bg-surface-elevated p-1"><button aria-label="Mes anterior" onClick={()=>setMonth(moveMonth(month,-1))} className="rounded-lg p-2 text-stone hover:bg-white/5 hover:text-on-dark"><ChevronLeft size={16}/></button><span className="financial-number w-24 text-center text-xs font-medium">{month}</span><button aria-label="Mes siguiente" onClick={()=>setMonth(moveMonth(month,1))} className="rounded-lg p-2 text-stone hover:bg-white/5 hover:text-on-dark"><ChevronRight size={16}/></button></div>}/>
    <div className="dashboard-grid"><div className="col-span-4"><KpiCard label="Gasto total" value={formatCurrency(expense)} hint="Mes seleccionado" icon={TrendingDown}/></div><div className="col-span-4"><KpiCard label="Ingreso total" value={formatCurrency(income)} hint="Mes seleccionado" icon={TrendingUp}/></div><div className="col-span-4"><KpiCard label="Tasa de ahorro" value={formatPercent(rate)} hint={`${formatCurrency(income-expense)} netos`} icon={Wallet}/></div></div>
    {!data?.by_category.length?<EmptyState icon={ReceiptText} title="No hay movimientos este mes" description="Importa o registra movimientos para ver el desglose por categoría y tu tasa de ahorro."/>:<div className="dashboard-grid">
      <ChartCard className="col-span-8" title="Gasto por categoría" description="Importe y peso sobre el gasto mensual"><div className="space-y-5">{data.by_category.map((cat,i)=><div key={cat.category_id??cat.category}><div className="flex items-center justify-between gap-4"><div className="flex items-center gap-2 text-sm"><span className="h-2.5 w-2.5 rounded-full" style={{background:COLORS[i%COLORS.length]}}/><span>{cat.category}</span></div><div className="financial-number text-right text-sm"><span>{formatCurrency(cat.amount)}</span><span className="ml-3 inline-block w-14 text-stone">{formatPercent(cat.percentage/100)}</span></div></div><div className="mt-2.5 h-2 rounded-full bg-white/5 overflow-hidden"><div className="h-full rounded-full transition-all" style={{width:`${Math.max(2,cat.percentage)}%`,background:COLORS[i%COLORS.length]}}/></div></div>)}</div></ChartCard>
      <ChartCard className="col-span-4" title="Lectura rápida" description="Señales del periodo"><div className="space-y-4"><div className="rounded-xl bg-primary/10 p-4"><p className="text-xs text-primary-bright">Mayor categoría</p><p className="mt-2 font-semibold">{data.by_category[0]?.category}</p><p className="mt-1 text-sm text-stone">Representa {formatPercent((data.by_category[0]?.percentage??0)/100)} del gasto.</p></div><p className="text-sm leading-6 text-stone">Las barras mantienen visibles las categorías pequeñas y permiten comparar importes sin depender únicamente del color.</p></div></ChartCard>
    </div>}
  </div>;
}
