import { RefreshCw } from "lucide-react";
import { useCallback, useState } from "react";
import { ErrorState, LoadingState, PageHeader } from "@/components/ui/Dashboard";
import { InsightFilters } from "./components/InsightFilters";
import { InsightList } from "./components/InsightList";
import { MonthlyReviewCard } from "./components/MonthlyReviewCard";
import { DataQualityCard } from "./components/DataQualityCard";
import { EmptyInsightsState } from "./components/EmptyInsightsState";
import { PartialDataNotice } from "./components/PartialDataNotice";
import { useInsights } from "./hooks/useInsights";
import { useMonthlyReview } from "./hooks/useMonthlyReview";
import { useDismissInsight } from "./hooks/useDismissInsight";
import type { InsightSeverity, InsightType } from "./types/insights.types";

const PERIODS = Array.from({ length: 12 }, (_, i) => {
  const d = new Date();
  d.setMonth(d.getMonth() - i);
  return d.toISOString().slice(0, 7);
});

export default function InsightsPage() {
  const [period, setPeriod] = useState<string>(PERIODS[0]);
  const [typeFilter, setTypeFilter] = useState<InsightType | "">("");
  const [severityFilter, setSeverityFilter] = useState<InsightSeverity | "">("");
  const [impactArea, setImpactArea] = useState<string>("");
  const [dismissedIds, setDismissedIds] = useState<Set<string>>(new Set());

  const { data, loading, error, refresh } = useInsights(
    {
      period,
      type: typeFilter || undefined,
      severity: severityFilter || undefined,
      impact_area: impactArea || undefined,
      limit: 10,
    },
    [period, typeFilter, severityFilter, impactArea],
  );

  const { data: review, loading: reviewLoading } = useMonthlyReview(period);

  const { dismiss } = useDismissInsight(useCallback((id: string) => {
    setDismissedIds((prev) => new Set([...prev, id]));
  }, []));

  const visibleInsights = (data?.insights ?? []).filter((i) => !dismissedIds.has(i.id));
  const dqInsights = visibleInsights.filter((i) => i.type === "data_quality");
  const mainInsights = visibleInsights.filter((i) => i.type !== "data_quality");
  const isPartial = data?.data_status === "partial" || data?.data_status === "insufficient";
  const isEmpty = data?.data_status === "empty" && !loading;

  return (
    <div className="p-8 max-w-[1500px] mx-auto space-y-6">
      <PageHeader
        eyebrow="Inteligencia financiera"
        title="Insights"
        description="Señales relevantes detectadas en tus finanzas."
        actions={
          <div className="flex items-center gap-3">
            <select
              value={period}
              onChange={(e) => setPeriod(e.target.value)}
              style={{ colorScheme: "dark", backgroundColor: "#1c1c1e", color: "#f5f5f0" }}
              className="rounded-lg border border-hairline-dark px-3 py-2 text-xs appearance-none cursor-pointer"
            >
              {PERIODS.map((p) => <option key={p} value={p} style={{ backgroundColor: "#1c1c1e", color: "#f5f5f0" }}>{p}</option>)}
            </select>
            <button
              onClick={refresh}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-lg bg-white/5 px-3 py-2 text-xs text-on-dark hover:bg-white/10 disabled:opacity-50 transition-colors"
            >
              <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
              Actualizar
            </button>
          </div>
        }
      />

      {data && !loading && (
        <div className="flex gap-3 flex-wrap">
          {data.summary.positive > 0 && <span className="rounded-full bg-accent-teal/10 px-3 py-1 text-xs text-accent-teal">{data.summary.positive} positivo{data.summary.positive !== 1 ? "s" : ""}</span>}
          {data.summary.warning > 0 && <span className="rounded-full bg-amber-400/10 px-3 py-1 text-xs text-amber-300">{data.summary.warning} atención</span>}
          {data.summary.critical > 0 && <span className="rounded-full bg-accent-danger/10 px-3 py-1 text-xs text-accent-danger">{data.summary.critical} crítico{data.summary.critical !== 1 ? "s" : ""}</span>}
          {data.summary.info > 0 && <span className="rounded-full bg-sky-400/10 px-3 py-1 text-xs text-sky-300">{data.summary.info} informativo{data.summary.info !== 1 ? "s" : ""}</span>}
        </div>
      )}

      {loading && <LoadingState label="Calculando insights financieros" />}

      {error && !loading && (
        <ErrorState
          title="No se han podido generar los insights"
          description="Inténtalo de nuevo o revisa el estado del backend."
          onRetry={refresh}
        />
      )}

      {!loading && !error && isEmpty && <EmptyInsightsState />}

      {!loading && !error && !isEmpty && (
        <div className="space-y-6">
          {review && !reviewLoading && <MonthlyReviewCard review={review} />}

          {isPartial && <PartialDataNotice />}

          <div className="space-y-4">
            <InsightFilters
              type={typeFilter}
              severity={severityFilter}
              impactArea={impactArea}
              onChange={({ type, severity, impactArea: area }) => {
                if (type !== undefined) setTypeFilter(type ?? "");
                if (severity !== undefined) setSeverityFilter(severity ?? "");
                if (area !== undefined) setImpactArea(area);
              }}
            />
            {mainInsights.length > 0 ? (
              <InsightList insights={mainInsights} onDismiss={dismiss} />
            ) : (
              <p className="text-sm text-stone py-4">No hay insights para los filtros seleccionados.</p>
            )}
          </div>

          {dqInsights.length > 0 && <DataQualityCard insights={dqInsights} />}
        </div>
      )}
    </div>
  );
}
