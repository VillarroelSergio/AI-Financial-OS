import { useMemo, useState } from "react";
import { BarChart3, CalendarDays, ChevronLeft, ChevronRight, ReceiptText, TrendingDown, TrendingUp, Wallet } from "lucide-react";
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { ChartCard, EmptyState, KpiCard, LoadingState, PageHeader } from "@/components/ui/Dashboard";
import { useSpending, useSpendingYears } from "@/lib/hooks/useDashboard";
import { formatCurrency, formatPercent } from "@/lib/formatters/currency";
import type { CategorySpending } from "@/lib/api/dashboard";
import ExpenseCategoryDetailDrawer from "./ExpenseCategoryDetailDrawer";

const COLORS = ["#7c83ff", "#2ad2a0", "#f4b95f", "#ff5f74", "#58c9f7", "#a3a8ff"];
const currentMonth = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`; };
const moveMonth = (value: string, delta: number) => { const [y, m] = value.split("-").map(Number); const d = new Date(y, m - 1 + delta, 1); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`; };

export default function SpendingPage() {
  const [month, setMonth] = useState(currentMonth);
  const initialYear = Number(currentMonth().slice(0, 4));
  const [year, setYear] = useState(initialYear);
  const [mode, setMode] = useState<"month" | "year">("month");
  const [selectedCategory, setSelectedCategory] = useState<CategorySpending | null>(null);
  const loadedYears = useSpendingYears();
  const yearOptions = loadedYears.length ? loadedYears : [year];
  const { data, loading } = useSpending({ mode, month, year });
  const expense = Number(data?.total_expense ?? 0);
  const income = Number(data?.total_income ?? 0);
  const net = Number(data?.net_savings ?? income - expense);
  const categories = useMemo(() => {
    const source = data?.by_category ?? [];
    const major = source.filter((cat) => cat.percentage >= 3).slice(0, 7);
    const minor = source.filter((cat) => !major.includes(cat));
    if (!minor.length) return major;
    const other = minor.reduce<CategorySpending>((acc, cat) => ({
      ...acc,
      amount: String(Number(acc.amount) + Number(cat.amount)),
      percentage: acc.percentage + cat.percentage,
    }), { category: "Otros", category_id: "otros", amount: "0", percentage: 0 });
    return [...major, other];
  }, [data]);

  if (loading) return <LoadingState label="Analizando el periodo" />;

  return (
    <div className="p-8 max-w-[1500px] mx-auto space-y-6">
      <ExpenseCategoryDetailDrawer
        category={selectedCategory}
        period={{ mode, month, year }}
        onClose={() => setSelectedCategory(null)}
      />
      <PageHeader
        eyebrow="Flujo mensual"
        title="Gastos"
        description="Desglose del gasto, ahorro neto y peso real de cada categoria."
        actions={
          <div className="flex items-center gap-2">
            <div className="flex rounded-lg border border-hairline-dark bg-white/[.035] p-1">
              {(["month", "year"] as const).map((item) => (
                <button key={item} onClick={() => setMode(item)} className={`rounded-lg px-3 py-2 text-xs ${mode === item ? "bg-primary text-on-primary" : "text-stone hover:text-on-dark"}`}>
                  {item === "month" ? "Mes" : "Ano"}
                </button>
              ))}
            </div>
            {mode === "month" ? (
              <div className="flex items-center rounded-lg border border-hairline-dark bg-white/[.035] p-1">
                <button aria-label="Mes anterior" onClick={() => setMonth(moveMonth(month, -1))} className="rounded-lg p-2 text-stone hover:bg-white/5 hover:text-on-dark"><ChevronLeft size={16} /></button>
                <input type="month" value={month} onChange={(e) => { setMonth(e.target.value); setYear(Number(e.target.value.slice(0, 4))); }} className="financial-number w-32 bg-transparent text-center text-xs font-medium text-on-dark outline-none" />
                <button aria-label="Mes siguiente" onClick={() => setMonth(moveMonth(month, 1))} className="rounded-lg p-2 text-stone hover:bg-white/5 hover:text-on-dark"><ChevronRight size={16} /></button>
              </div>
            ) : (
              <select value={year} onChange={(e) => setYear(Number(e.target.value))} className="rounded-lg border border-hairline-dark bg-white/[.035] px-4 py-2 text-xs font-medium text-on-dark outline-none">
                {yearOptions.map((option) => <option key={option} value={option}>{option}</option>)}
              </select>
            )}
          </div>
        }
      />

      <div className="dashboard-grid">
        <div className="col-span-3"><KpiCard label="Gasto total" value={formatCurrency(expense)} hint="Periodo seleccionado" icon={TrendingDown} positive={false} /></div>
        <div className="col-span-3"><KpiCard label="Ingreso total" value={formatCurrency(income)} hint="Periodo seleccionado" icon={TrendingUp} /></div>
        <div className="col-span-3"><KpiCard label="Ahorro neto" value={formatCurrency(net)} delta={formatPercent((data?.savings_rate ?? 0) / 100)} hint="tasa de ahorro" icon={Wallet} positive={net >= 0} /></div>
        <div className="col-span-3"><KpiCard label="Gasto medio diario" value={formatCurrency(data?.average_daily_expense ?? "0")} hint={`${data?.transaction_count ?? 0} transacciones`} icon={CalendarDays} /></div>
      </div>

      {!categories.length ? (
        <EmptyState icon={ReceiptText} title="No hay movimientos este periodo" description="Importa o registra movimientos para ver porcentajes por categoria y evolucion de ahorro." />
      ) : (
        <div className="dashboard-grid">
          <ChartCard className="col-span-4" title="Porcentaje por categoria" description="Categorias pequenas agrupadas en Otros">
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categories}
                    dataKey="percentage"
                    nameKey="category"
                    cx="50%"
                    cy="50%"
                    innerRadius={56}
                    outerRadius={88}
                    paddingAngle={2}
                    label={({ payload }) => {
                      const cat = payload as { category?: string; percentage?: number };
                      return `${cat.category ?? ""} ${Number(cat.percentage ?? 0).toFixed(1)}%`;
                    }}
                    labelLine={false}
                    fontSize={10}
                    onClick={(entry) => setSelectedCategory(entry as unknown as CategorySpending)}
                    className="cursor-pointer"
                  >
                    {categories.map((cat, index) => <Cell key={cat.category_id ?? cat.category} fill={COLORS[index % COLORS.length]} />)}
                  </Pie>
                  <Tooltip formatter={(value, _name, item) => [`${Number(value).toFixed(1)}%`, item.payload.category]} contentStyle={{ background: "#16181a", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 8, color: "#fff", fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </ChartCard>

          <ChartCard className="col-span-8" title="Gasto por categoria" description="Importe y porcentaje sobre el gasto mensual">
            <div className="space-y-5">
              {categories.map((cat, index) => (
                <button key={cat.category_id ?? cat.category} type="button" onClick={() => setSelectedCategory(cat)} className="block w-full rounded-lg text-left transition-colors hover:bg-white/[0.03] focus:outline-none focus:ring-1 focus:ring-primary">
                  <div className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-2 text-sm min-w-0">
                      <span className="h-2.5 w-2.5 rounded-full shrink-0" style={{ background: COLORS[index % COLORS.length] }} />
                      <span className="truncate">{cat.category}</span>
                    </div>
                    <div className="financial-number text-right text-sm shrink-0">
                      <span>{formatCurrency(cat.amount)}</span>
                      <span className="ml-3 inline-block w-16 text-stone">{cat.percentage.toFixed(1)}%</span>
                    </div>
                  </div>
                  <div className="mt-2.5 h-2 rounded-full bg-white/5 overflow-hidden">
                    <div className="h-full rounded-full transition-all" style={{ width: `${Math.max(2, cat.percentage)}%`, background: COLORS[index % COLORS.length] }} />
                  </div>
                </button>
              ))}
            </div>
          </ChartCard>

          <ChartCard className="col-span-8" title={mode === "year" ? "Evolucion anual" : "Lectura del periodo"} description="Resumen claro sin mezclar bases de calculo">
            <div className="grid grid-cols-3 gap-4">
              <div className="rounded-lg border border-hairline-dark bg-primary/10 p-4">
                <p className="text-xs text-primary-bright">Mayor categoria</p>
                <p className="mt-2 font-semibold">{categories[0]?.category}</p>
                <p className="mt-1 text-sm text-stone">{categories[0]?.percentage.toFixed(1)}% del gasto.</p>
              </div>
              <div className="rounded-lg border border-hairline-dark bg-white/[.035] p-4">
                <p className="text-xs text-stone">Base del porcentaje</p>
                <p className="mt-2 font-semibold">{formatCurrency(expense)}</p>
                <p className="mt-1 text-sm text-stone">Cada categoria se divide entre el gasto total.</p>
              </div>
              <div className="rounded-lg border border-hairline-dark bg-white/[.035] p-4">
                <p className="text-xs text-stone">Vista activa</p>
                <p className="mt-2 font-semibold">{mode === "month" ? "Mes" : "Ano"}</p>
                <p className="mt-1 text-sm text-stone">{mode === "month" ? month : year}</p>
              </div>
            </div>
          </ChartCard>
          <ChartCard className="col-span-4" title="Control visual" description="Comparacion rapida">
            <div className="flex h-44 items-end gap-3">
              {categories.slice(0, 6).map((cat, index) => (
                <button key={cat.category_id ?? cat.category} type="button" onClick={() => setSelectedCategory(cat)} className="flex flex-1 flex-col items-center gap-2 rounded-lg transition-colors hover:bg-white/[0.03] focus:outline-none focus:ring-1 focus:ring-primary">
                  <div className="w-full rounded-t-lg" style={{ height: `${Math.max(10, cat.percentage * 1.4)}px`, background: COLORS[index % COLORS.length] }} />
                  <div className="flex min-h-10 flex-col items-center justify-start gap-1 text-center">
                    <BarChart3 size={14} className="text-stone" />
                    <span className="max-w-full truncate text-[10px] text-stone" title={cat.category}>{cat.category}</span>
                    <span className="financial-number text-[10px] text-on-dark">{cat.percentage.toFixed(1)}%</span>
                  </div>
                </button>
              ))}
            </div>
          </ChartCard>
        </div>
      )}
    </div>
  );
}
