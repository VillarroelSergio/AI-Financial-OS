import { useMemo, useState } from "react";
import { CalendarDays, ChevronLeft, ChevronRight, ReceiptText, TrendingDown, TrendingUp, Wallet } from "lucide-react";
import { Bar, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { ChartCard, EmptyState, KpiCard, LoadingState, PageHeader } from "@/components/ui/Dashboard";
import { CATEGORY_CHART_COLORS, CategoryIcon, getCategoryAccent, type CategoryVisual } from "@/components/ui/CategoryBadge";
import { useSpending, useSpendingMonthly, useSpendingYears } from "@/lib/hooks/useDashboard";
import { useCategories } from "@/lib/hooks/useCategories";
import { formatCurrency, formatPercent } from "@/lib/formatters/currency";
import type { CategorySpending } from "@/lib/api/dashboard";
import ExpenseCategoryDetailDrawer from "./ExpenseCategoryDetailDrawer";

const MONTH_LABEL = new Intl.DateTimeFormat("es-ES", { month: "short" });
const currentMonth = () => { const d = new Date(); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`; };
const moveMonth = (value: string, delta: number) => { const [y, m] = value.split("-").map(Number); const d = new Date(y, m - 1 + delta, 1); return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`; };

export default function SpendingPage() {
  const [month, setMonth] = useState(currentMonth);
  const initialYear = Number(currentMonth().slice(0, 4));
  const [year, setYear] = useState(initialYear);
  const [mode, setMode] = useState<"month" | "year">("month");
  const [selectedCategory, setSelectedCategory] = useState<CategorySpending | null>(null);
  const { income: INCOME_COLOR, expense: EXPENSE_COLOR, savings: SAVINGS_LINE } = CATEGORY_CHART_COLORS;
  const loadedYears = useSpendingYears();
  const yearOptions = loadedYears.length ? loadedYears : [year];
  const { data, loading } = useSpending({ mode, month, year });
  const { categories: categoryDefinitions } = useCategories();
  const categoryDefinitionsById = useMemo(
    () => new Map(categoryDefinitions.map((category) => [category.id, category])),
    [categoryDefinitions],
  );
  const monthly = useSpendingMonthly(12, mode === "year" ? year : undefined);
  const trendData = useMemo(
    () =>
      monthly.map((p) => ({
        month: p.month,
        label: MONTH_LABEL.format(new Date(`${p.month}-01T00:00:00`)),
        income: Number(p.income),
        expense: Number(p.expense),
        savings: Number(p.savings),
      })),
    [monthly],
  );
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
  const categoryVisual = (category: CategorySpending): CategoryVisual =>
    (category.category_id ? categoryDefinitionsById.get(category.category_id) : undefined)
    ?? { name: category.category, type: "expense" };

  if (loading) return <LoadingState label="Analizando el periodo" />;

  return (
    <div className="page-shell space-y-6">
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
            <div className="flex rounded-lg border border-hairline-dark bg-[var(--bg-interactive)] p-1">
              {(["month", "year"] as const).map((item) => (
                <button key={item} onClick={() => setMode(item)} className={`rounded-lg px-3 py-2 text-xs ${mode === item ? "bg-primary text-on-primary" : "text-stone hover:text-on-dark"}`}>
                  {item === "month" ? "Mes" : "Ano"}
                </button>
              ))}
            </div>
            {mode === "month" ? (
              <div className="flex items-center rounded-lg border border-hairline-dark bg-[var(--bg-interactive)] p-1">
                <button aria-label="Mes anterior" onClick={() => setMonth(moveMonth(month, -1))} className="rounded-lg p-2 text-stone hover:bg-[var(--bg-interactive)] hover:text-on-dark"><ChevronLeft size={16} /></button>
                <input type="month" value={month} onChange={(e) => { setMonth(e.target.value); setYear(Number(e.target.value.slice(0, 4))); }} className="financial-number w-32 bg-transparent text-center text-xs font-medium text-on-dark outline-none" />
                <button aria-label="Mes siguiente" onClick={() => setMonth(moveMonth(month, 1))} className="rounded-lg p-2 text-stone hover:bg-[var(--bg-interactive)] hover:text-on-dark"><ChevronRight size={16} /></button>
              </div>
            ) : (
              <select value={year} onChange={(e) => setYear(Number(e.target.value))} className="rounded-lg border border-hairline-dark bg-[var(--bg-interactive)] px-4 py-2 text-xs font-medium text-on-dark outline-none">
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
          <ChartCard className="col-span-6" title="Evolucion mensual" description={mode === "year" ? `Gasto e ingreso del ano ${year}; haz click en un mes para verlo en detalle` : "Gasto e ingreso de los ultimos 12 meses; haz click en un mes para verlo en detalle"}>
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={trendData} barGap={2} onClick={(state) => {
                  const payload = (state as { activePayload?: { payload?: { month?: string } }[] })?.activePayload;
                  const m = payload?.[0]?.payload?.month;
                  if (m) { setMode("month"); setMonth(m); setYear(Number(m.slice(0, 4))); }
                }}>
                  <XAxis dataKey="label" tick={{ fill: "var(--text-secondary)", fontSize: 11 }} axisLine={false} tickLine={false} />
                  <YAxis tick={{ fill: "var(--text-secondary)", fontSize: 11 }} axisLine={false} tickLine={false} width={54} tickFormatter={(v: number) => `${Math.round(v)}€`} />
                  <Tooltip
                    formatter={(value, name) => [formatCurrency(Number(value)), name === "expense" ? "Gasto" : name === "income" ? "Ingreso" : "Ahorro"]}
                    labelFormatter={(label, payload) => payload?.[0]?.payload?.month ?? label}
                    contentStyle={{ background: "var(--bg-card)", border: "1px solid var(--border-soft)", borderRadius: 8, color: "var(--text-primary)", fontSize: 12 }}
                    cursor={{ fill: "var(--divider-soft)" }}
                  />
                  <Bar dataKey="income" fill={INCOME_COLOR} radius={[4, 4, 0, 0]} maxBarSize={16} className="cursor-pointer" />
                  <Bar dataKey="expense" fill={EXPENSE_COLOR} radius={[4, 4, 0, 0]} maxBarSize={16} className="cursor-pointer" />
                  <Line dataKey="savings" stroke={SAVINGS_LINE} strokeWidth={2} dot={false} type="monotone" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
            <div className="mt-3 flex items-center gap-5 text-xs text-stone">
              <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm" style={{ background: INCOME_COLOR }} />Ingreso</span>
              <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm" style={{ background: EXPENSE_COLOR }} />Gasto</span>
              <span className="flex items-center gap-1.5"><span className="inline-block h-0.5 w-3.5" style={{ background: SAVINGS_LINE }} />Ahorro</span>
            </div>
          </ChartCard>

          <ChartCard className="col-span-6" title="Gasto por categoria" description="Importe y porcentaje sobre el gasto del periodo">
            <div className="space-y-5">
              {categories.map((cat) => {
                const visual = categoryVisual(cat);
                const accent = getCategoryAccent(visual);
                return (
                  <button key={cat.category_id ?? cat.category} type="button" onClick={() => setSelectedCategory(cat)} className="block w-full rounded-lg text-left transition-colors hover:bg-[var(--bg-interactive)] focus:outline-none focus:ring-1 focus:ring-primary">
                    <div className="flex items-center justify-between gap-4">
                      <span className="flex min-w-0 items-center gap-2 text-sm">
                        <CategoryIcon category={visual} />
                        <span className="truncate">{cat.category}</span>
                      </span>
                      <div className="financial-number text-right text-sm shrink-0">
                        <span>{formatCurrency(cat.amount)}</span>
                        <span className="ml-3 inline-block w-16 text-stone">{cat.percentage.toFixed(1)}%</span>
                      </div>
                    </div>
                    <div className="mt-2.5 h-2 rounded-full bg-[var(--bg-interactive)] overflow-hidden">
                      <div className="progress-fill h-full rounded-full" style={{ transform: `scaleX(${Math.max(2, cat.percentage) / 100})`, background: accent }} />
                    </div>
                  </button>
                );
              })}
            </div>
          </ChartCard>

          <ChartCard className="col-span-12" title="Lectura del periodo" description="Resumen claro sin mezclar bases de calculo">
            <div className="grid grid-cols-3 gap-4">
              <div className="rounded-lg border border-hairline-dark bg-primary/10 p-4">
                <p className="text-xs text-primary-bright">Mayor categoria</p>
                <p className="mt-2 font-semibold">{categories[0]?.category}</p>
                <p className="mt-1 text-sm text-stone">{categories[0]?.percentage.toFixed(1)}% del gasto.</p>
              </div>
              <div className="rounded-lg border border-hairline-dark bg-[var(--bg-interactive)] p-4">
                <p className="text-xs text-stone">Base del porcentaje</p>
                <p className="mt-2 font-semibold">{formatCurrency(expense)}</p>
                <p className="mt-1 text-sm text-stone">Cada categoria se divide entre el gasto total.</p>
              </div>
              <div className="rounded-lg border border-hairline-dark bg-[var(--bg-interactive)] p-4">
                <p className="text-xs text-stone">Vista activa</p>
                <p className="mt-2 font-semibold">{mode === "month" ? "Mes" : "Ano"}</p>
                <p className="mt-1 text-sm text-stone">{mode === "month" ? month : year}</p>
              </div>
            </div>
          </ChartCard>
        </div>
      )}
    </div>
  );
}
