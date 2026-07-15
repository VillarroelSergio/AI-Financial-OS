import { ArrowRight, Sparkles } from "lucide-react";
import { useNavigate } from "react-router-dom";
import type { Insight } from "@/features/insights/types/insights.types";

export default function InsightStrip({ insights }: { insights: Insight[] }) {
  const navigate = useNavigate();
  if (insights.length === 0) return null;

  return (
    <div className="grid gap-3 md:grid-cols-2">
      {insights.slice(0, 2).map((insight) => {
        const target = insight.actions[0]?.target ?? "/insights";
        return (
          <article key={insight.id} className="premium-card flex items-center gap-3 rounded-2xl px-4 py-3">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-[10px] bg-[var(--primary)]/10 text-[var(--primary)]">
              <Sparkles size={16} />
            </span>
            <div className="min-w-0 flex-1">
              <p
                className="truncate text-[13px] text-[var(--text-secondary)]"
                title={`${insight.title}${insight.summary ? ` · ${insight.summary}` : ""}`}
              >
                <span className="font-semibold text-[var(--text-primary)]">{insight.title}</span>
                {insight.summary ? ` · ${insight.summary}` : ""}
              </p>
            </div>
            <button
              onClick={() => navigate(target)}
              className="flex min-h-[24px] shrink-0 items-center gap-1 px-1 text-[12px] font-medium text-[var(--primary)] hover:underline"
            >
              Ver desglose <ArrowRight size={13} />
            </button>
          </article>
        );
      })}
    </div>
  );
}
