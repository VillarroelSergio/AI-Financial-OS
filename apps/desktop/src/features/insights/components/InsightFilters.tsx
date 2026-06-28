import type { InsightType, InsightSeverity } from "../types/insights.types";

const TYPES: { value: InsightType | ""; label: string }[] = [
  { value: "", label: "Todos los tipos" },
  { value: "spending_anomaly", label: "Gasto anómalo" },
  { value: "monthly_comparison", label: "Comparativa mensual" },
  { value: "savings_rate", label: "Tasa de ahorro" },
  { value: "cashflow_alert", label: "Flujo de caja" },
  { value: "net_worth_change", label: "Patrimonio" },
  { value: "investment_allocation", label: "Inversiones" },
  { value: "goal_progress", label: "Objetivos" },
  { value: "market_context", label: "Mercado" },
  { value: "macro_context", label: "Macro" },
  { value: "data_quality", label: "Calidad de datos" },
];

const SEVERITIES: { value: InsightSeverity | ""; label: string }[] = [
  { value: "", label: "Toda severidad" },
  { value: "positive", label: "Positivo" },
  { value: "info", label: "Información" },
  { value: "warning", label: "Atención" },
  { value: "critical", label: "Crítico" },
];

const AREAS = [
  { value: "", label: "Todas las áreas" },
  { value: "spending", label: "Gastos" },
  { value: "patrimonio", label: "Patrimonio" },
  { value: "inversiones", label: "Inversiones" },
  { value: "objetivos", label: "Objetivos" },
  { value: "mercado", label: "Mercado" },
  { value: "macro", label: "Macro" },
  { value: "calidad", label: "Calidad de datos" },
];

interface InsightFiltersProps {
  type: InsightType | "";
  severity: InsightSeverity | "";
  impactArea: string;
  onChange: (updates: { type?: InsightType | ""; severity?: InsightSeverity | ""; impactArea?: string }) => void;
}

function Select({ value, options, onChange }: { value: string; options: { value: string; label: string }[]; onChange: (v: string) => void }) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      style={{ colorScheme: "dark", backgroundColor: "#1c1c1e", color: "#f5f5f0" }}
      className="rounded-lg border border-hairline-dark px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-primary appearance-none cursor-pointer"
    >
      {options.map((o) => <option key={o.value} value={o.value} style={{ backgroundColor: "#1c1c1e", color: "#f5f5f0" }}>{o.label}</option>)}
    </select>
  );
}

export function InsightFilters({ type, severity, impactArea, onChange }: InsightFiltersProps) {
  return (
    <div className="flex flex-wrap gap-2">
      <Select value={type} options={TYPES} onChange={(v) => onChange({ type: v as InsightType | "" })} />
      <Select value={severity} options={SEVERITIES} onChange={(v) => onChange({ severity: v as InsightSeverity | "" })} />
      <Select value={impactArea} options={AREAS} onChange={(v) => onChange({ impactArea: v })} />
    </div>
  );
}
