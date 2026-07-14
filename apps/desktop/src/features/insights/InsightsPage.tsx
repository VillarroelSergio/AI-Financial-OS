import { RefreshCw, Undo2 } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ErrorState, LoadingState, PageHeader } from "@/components/ui/Dashboard";
import { getCopilotContext } from "@/features/assistant/contextualCopilot";
import { InsightFilters } from "./components/InsightFilters";
import { InsightList } from "./components/InsightList";
import { MonthlyReviewCard } from "./components/MonthlyReviewCard";
import { DataQualityCard } from "./components/DataQualityCard";
import { EmptyInsightsState } from "./components/EmptyInsightsState";
import { PartialDataNotice } from "./components/PartialDataNotice";
import { useInsights } from "./hooks/useInsights";
import { useMonthlyReview } from "./hooks/useMonthlyReview";
import { useDismissInsight } from "./hooks/useDismissInsight";
import type { Insight, InsightSeverity, InsightType } from "./types/insights.types";

const PERIODS = Array.from({ length: 12 }, (_, i) => {
  const d = new Date();
  d.setMonth(d.getMonth() - i);
  return d.toISOString().slice(0, 7);
});

// INS-7 / INS-F2: chips de severidad clicables con conteos vivos (sustituyen al dropdown).
const SEVERITY_CHIPS: { key: InsightSeverity; label: (n: number) => string; cls: string; ring: string }[] = [
  { key: "critical", label: (n) => `${n} crítico${n !== 1 ? "s" : ""}`, cls: "bg-accent-danger/10 text-accent-danger", ring: "ring-accent-danger" },
  { key: "warning", label: () => "atención", cls: "bg-amber-400/10 text-amber-300", ring: "ring-amber-400" },
  { key: "positive", label: (n) => `${n} positivo${n !== 1 ? "s" : ""}`, cls: "bg-accent-teal/10 text-accent-teal", ring: "ring-accent-teal" },
  { key: "info", label: (n) => `${n} informativo${n !== 1 ? "s" : ""}`, cls: "bg-sky-400/10 text-sky-300", ring: "ring-sky-400" },
];

export default function InsightsPage() {
  const navigate = useNavigate();
  const [period, setPeriod] = useState<string>(PERIODS[0]);
  const [typeFilter, setTypeFilter] = useState<InsightType | "">("");
  const [severityFilter, setSeverityFilter] = useState<InsightSeverity | "">("");
  const [impactArea, setImpactArea] = useState<string>("");
  const [dismissedIds, setDismissedIds] = useState<Set<string>>(new Set());
  const [lastDismissedId, setLastDismissedId] = useState<string | null>(null);

  // La severidad se filtra en cliente (chips) para que los conteos no colapsen al filtrar.
  const { data, loading, error, regenerate } = useInsights(
    {
      period,
      type: typeFilter || undefined,
      impact_area: impactArea || undefined,
      limit: 10,
    },
    [period, typeFilter, impactArea],
  );

  const { data: review, loading: reviewLoading } = useMonthlyReview(period);

  const { dismiss, restore } = useDismissInsight(useCallback((id: string) => {
    setDismissedIds((prev) => new Set([...prev, id]));
    setLastDismissedId(id);
  }, []));

  const undoDismiss = useCallback(() => {
    setLastDismissedId((id) => {
      if (id) {
        restore(id);
        setDismissedIds((prev) => {
          const next = new Set(prev);
          next.delete(id);
          return next;
        });
      }
      return null;
    });
  }, [restore]);

  // INS-8: "Explicar" abre el asistente con el insight como contexto (patrón contextualCopilot / RootLayout).
  const askAI = useCallback((insight: Insight) => {
    const context = getCopilotContext("/insights");
    const prompt = `Explícame este insight: "${insight.title}". ${insight.summary} Usa get_insights_summary y, si aplica, get_balance_sheet; explica sin recalcular las cifras.`;
    navigate("/assistant", { state: { prompt, context: { ...context, insight_id: insight.id, period } } });
  }, [navigate, period]);

  // El banner de deshacer se auto-oculta a los 6 s.
  useEffect(() => {
    if (!lastDismissedId) return;
    const t = setTimeout(() => setLastDismissedId(null), 6000);
    return () => clearTimeout(t);
  }, [lastDismissedId]);

  const visibleInsights = (data?.insights ?? []).filter((i) => !dismissedIds.has(i.id));
  // Taxonomía de tres clases (INS-2/INS-7): señales accionables, contexto, calidad de datos.
  const dqInsights = visibleInsights.filter((i) => i.insight_class === "data_quality");
  const contextInsights = visibleInsights.filter((i) => i.insight_class === "context");
  const signals = visibleInsights.filter((i) => i.insight_class === "signal");

  // Conteos vivos sobre las señales (no sobre el summary del servidor, que se recorta al filtrar).
  const severityCounts = useMemo(() => {
    const c: Record<InsightSeverity, number> = { positive: 0, info: 0, warning: 0, critical: 0 };
    for (const s of signals) c[s.severity] += 1;
    return c;
  }, [signals]);

  const mainInsights = severityFilter ? signals.filter((s) => s.severity === severityFilter) : signals;
  const lastDismissedTitle = data?.insights.find((i) => i.id === lastDismissedId)?.title;
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
            {/* regenerate ejecuta refreshInsights en el hook; no reutiliza la lectura cacheada. */}
            <button
              onClick={regenerate}
              disabled={loading}
              className="inline-flex items-center gap-2 rounded-lg bg-white/5 px-3 py-2 text-xs text-on-dark hover:bg-white/10 disabled:opacity-50 transition-colors"
            >
              <RefreshCw size={13} className={loading ? "animate-spin" : ""} />
              Actualizar
            </button>
            {data?.generated_at && <span className="text-xs text-stone">Actualizado {new Date(data.generated_at).toLocaleString("es-ES", { dateStyle: "medium", timeStyle: "short" })}</span>}
          </div>
        }
      />

      {data && !loading && (
        <div className="flex gap-2 flex-wrap">
          {SEVERITY_CHIPS.map(({ key, label, cls, ring }) => {
            const count = severityCounts[key];
            if (count === 0) return null;
            const active = severityFilter === key;
            return (
              <button
                key={key}
                onClick={() => setSeverityFilter((f) => (f === key ? "" : key))}
                aria-pressed={active}
                className={`rounded-full px-3 py-1 text-xs transition-all ${cls} ${active ? `ring-1 ${ring}` : "opacity-80 hover:opacity-100"}`}
              >
                {key === "warning" ? `${count} atención` : label(count)}
              </button>
            );
          })}
          {severityFilter && (
            <button
              onClick={() => setSeverityFilter("")}
              className="rounded-full px-3 py-1 text-xs text-stone hover:text-on-dark transition-colors"
            >
              Quitar filtro
            </button>
          )}
        </div>
      )}

      {lastDismissedId && (
        <div className="flex items-center justify-between gap-3 rounded-lg border border-white/10 bg-white/5 px-4 py-2">
          <p className="text-xs text-stone truncate">
            Insight descartado{lastDismissedTitle ? `: ${lastDismissedTitle}` : ""}.
          </p>
          <button onClick={undoDismiss} className="inline-flex items-center gap-1.5 text-xs text-primary-bright hover:underline shrink-0">
            <Undo2 size={13} />
            Deshacer
          </button>
        </div>
      )}

      {loading && <LoadingState label="Calculando insights financieros" />}

      {error && !loading && (
        <ErrorState
          title="No se han podido generar los insights"
          description="No se han podido calcular las señales con tus datos locales. Comprueba que el backend esté disponible o importa movimientos de al menos un mes: necesitas datos suficientes para analizar tendencias."
          onRetry={regenerate}
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
              impactArea={impactArea}
              onChange={({ type, impactArea: area }) => {
                if (type !== undefined) setTypeFilter(type ?? "");
                if (area !== undefined) setImpactArea(area);
              }}
            />
            {mainInsights.length > 0 ? (
              <InsightList insights={mainInsights} onDismiss={dismiss} onAskAI={askAI} />
            ) : (
              <p className="text-sm text-stone py-4">No hay señales para los filtros seleccionados.</p>
            )}
          </div>

          {contextInsights.length > 0 && (
            <details className="premium-card rounded-xl border border-white/10 p-4" open>
              <summary className="cursor-pointer text-xs font-semibold text-stone uppercase tracking-wide">
                Contexto del mes ({contextInsights.length})
              </summary>
              <div className="mt-3 space-y-2">
                {contextInsights.map((i) => (
                  <div key={i.id} className="flex items-center justify-between gap-3 rounded-lg bg-white/5 px-3 py-2">
                    <div className="min-w-0">
                      <p className="text-sm text-on-dark truncate">{i.title}</p>
                      <p className="text-xs text-stone truncate">{i.summary}</p>
                    </div>
                    {i.primary_metric && (
                      <span className="shrink-0 text-sm font-semibold text-on-dark">
                        {i.primary_metric.unit === "%"
                          ? `${i.primary_metric.value.toLocaleString("es-ES", { minimumFractionDigits: i.primary_metric.precision ?? 1, maximumFractionDigits: i.primary_metric.precision ?? 1 })} %`
                          : i.primary_metric.value.toLocaleString("es-ES")}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </details>
          )}

          {dqInsights.length > 0 && <DataQualityCard insights={dqInsights} />}
        </div>
      )}
    </div>
  );
}
