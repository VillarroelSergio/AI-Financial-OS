import { X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import type { Insight } from "../types/insights.types";
import { InsightSeverityBadge } from "./InsightSeverityBadge";
import { InsightMetric } from "./InsightMetric";
import { InsightSourcesDisclosure } from "./InsightSourcesDisclosure";

const BORDER: Record<string, string> = {
  positive: "border-accent-teal/20",
  info: "border-sky-400/20",
  warning: "border-amber-400/20",
  critical: "border-accent-danger/20",
};

interface InsightCardProps {
  insight: Insight;
  onDismiss?: (id: string) => void;
  onAskAI?: (insight: Insight) => void;
  compact?: boolean;
}

export function InsightCard({ insight, onDismiss, onAskAI, compact = false }: InsightCardProps) {
  const navigate = useNavigate();
  const borderClass = BORDER[insight.severity] ?? "border-white/10";

  return (
    <article className={`premium-card rounded-xl border ${borderClass} p-5 space-y-3`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap">
          <InsightSeverityBadge severity={insight.severity} />
          <span className="text-[11px] text-stone">{insight.period}</span>
        </div>
        {onDismiss && (
          <button onClick={() => onDismiss(insight.id)} className="text-stone hover:text-on-dark transition-colors shrink-0">
            <X size={14} />
          </button>
        )}
      </div>

      <div>
        <h3 className="text-sm font-semibold text-on-dark">{insight.title}</h3>
        <p className="mt-1 text-sm text-stone">{insight.summary}</p>
        {!compact && insight.detail && (
          <p className="mt-1 text-xs text-mute">{insight.detail}</p>
        )}
      </div>

      {insight.primary_metric && (
        <InsightMetric metric={insight.primary_metric} large />
      )}

      {!compact && insight.secondary_metrics.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {insight.secondary_metrics.map((m, i) => <InsightMetric key={i} metric={m} />)}
        </div>
      )}

      <div className="flex items-center gap-2 flex-wrap pt-1">
        {insight.actions.map((action, i) => (
          <button
            key={i}
            onClick={() => navigate(action.target)}
            className="rounded-md bg-white/5 px-3 py-1.5 text-xs text-on-dark hover:bg-white/10 transition-colors"
          >
            {action.label}
          </button>
        ))}
        {onAskAI && (
          <button
            onClick={() => onAskAI(insight)}
            className="rounded-md bg-primary/10 px-3 py-1.5 text-xs text-primary-bright hover:bg-primary/20 transition-colors"
          >
            Preguntar a la IA
          </button>
        )}
      </div>

      {!compact && <InsightSourcesDisclosure sources={insight.sources} />}
    </article>
  );
}
