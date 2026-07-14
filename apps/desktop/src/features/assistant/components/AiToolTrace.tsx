import { useState } from "react";
import { ChevronDown, ChevronRight, Database } from "lucide-react";
import type { AiToolCall } from "../types/aiAssistant.types";

interface Props {
  toolCalls: AiToolCall[];
}

function statusColor(status: string) {
  if (status === "ok") return "text-green-400";
  if (status === "not_available") return "text-yellow-400";
  return "text-red-400";
}

// AI-2: nombre de tool → dato humano para el resumen "Datos usados: …".
const DATA_LABELS: Record<string, string> = {
  get_net_worth: "patrimonio",
  get_balance_sheet: "balance",
  get_monthly_summary: "resumen mensual",
  get_spending_by_category: "gasto por categoría",
  compare_periods: "comparativa de periodos",
  get_savings_rate: "tasa de ahorro",
  get_goal_progress: "objetivos",
  get_portfolio_summary: "cartera",
  get_asset_allocation: "distribución de activos",
  get_currency_exposure: "exposición por divisa",
  get_sector_exposure: "exposición por sector",
  get_macro_snapshot: "macro",
  get_personal_impact_summary: "impacto personal",
  get_financial_signals: "señales financieras",
  get_insights_summary: "insights",
  get_market_regime: "régimen de mercado",
  get_ai_datasheet: "contexto general",
};

function dataLabel(name: string): string {
  return DATA_LABELS[name] ?? name;
}

export default function AiToolTrace({ toolCalls }: Props) {
  const [expanded, setExpanded] = useState(false);

  if (!toolCalls.length) return null;

  // Datos consultados, en nombres humanos y sin duplicados (una tool puede llamarse varias veces).
  const usedData = [...new Set(toolCalls.map((tc) => dataLabel(tc.name)))];

  return (
    <div className="mt-2">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="flex items-center gap-1.5 text-caption text-stone hover:text-on-dark transition-colors text-left"
      >
        <Database size={12} className="flex-shrink-0" />
        <span>Datos usados: {usedData.join(", ")}</span>
        {expanded ? <ChevronDown size={12} className="flex-shrink-0" /> : <ChevronRight size={12} className="flex-shrink-0" />}
      </button>
      {expanded && (
        <div className="mt-2 space-y-1.5 pl-3 border-l border-hairline-dark">
          {toolCalls.map((tc, i) => (
            <div key={i} className="text-caption">
              <span className="text-stone">{dataLabel(tc.name)}</span>
              <span className={`font-mono ml-2 ${statusColor(tc.status)}`}>{tc.name}</span>
              {tc.duration_ms != null && (
                <span className="text-mute ml-2">{tc.duration_ms}ms</span>
              )}
              {tc.status === "error" && tc.result?.error != null && (
                <span className="text-red-400 ml-2">{String(tc.result.error)}</span>
              )}
              {tc.status === "not_available" && (
                <span className="text-yellow-400 ml-2">sin datos</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
