import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { AlertCircle, RefreshCw, Sparkles } from "lucide-react";
import { EmptyState } from "@/components/ui/Dashboard";
import { formatCurrency, formatNumber } from "@/lib/formatters/currency";
import { useBriefs } from "../hooks/useBriefs";
import type { AiBrief, AiKeyFigure } from "../types/aiAssistant.types";
import Markdown from "./Markdown";

const SEVERITY_DOT: Record<string, string> = {
  positive: "bg-accent-teal",
  info: "bg-primary",
  warning: "bg-accent-warning",
  critical: "bg-accent-danger",
};

const DATA_STATE_LABEL: Record<string, string> = {
  complete: "Datos completos",
  partial: "Datos parciales",
  insufficient: "Datos insuficientes",
  empty: "Sin datos",
  error: "Error de datos",
};

function formatFigure(fig: AiKeyFigure): string {
  if (fig.unit === "EUR") return formatCurrency(fig.value);
  if (fig.unit === "%") return `${fig.value.toFixed(1)} %`;
  return formatNumber(fig.value);
}

function TraceBadge({ brief }: { brief: AiBrief }) {
  const parts = [
    `Periodo ${brief.period}`,
    DATA_STATE_LABEL[brief.data_state] ?? brief.data_state,
    brief.model ? `${brief.provider} · ${brief.model}` : "Narrativa determinista (sin IA)",
  ];
  return (
    <p className="text-caption text-stone">{parts.join("  ·  ")}</p>
  );
}

function BriefHero({ brief }: { brief: AiBrief }) {
  const navigate = useNavigate();
  const { bundle } = brief;
  return (
    <div className="premium-card rounded-lg p-5 space-y-4">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h2 className="text-heading-sm text-on-dark">{bundle.headline}</h2>
          <TraceBadge brief={brief} />
        </div>
      </div>

      {bundle.key_figures.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {bundle.key_figures.map((fig) => (
            <div key={fig.label} className="rounded-lg bg-surface-elevated border border-hairline-dark p-3">
              <p className="text-caption text-stone">{fig.label}</p>
              <p className="text-body-md text-on-dark font-medium mt-0.5">{formatFigure(fig)}</p>
            </div>
          ))}
        </div>
      )}

      {brief.narrative ? (
        <Markdown content={brief.narrative} />
      ) : (
        <p className="text-body-sm text-stone">{bundle.summary}</p>
      )}

      {bundle.signals.length > 0 && (
        <div className="space-y-2">
          <p className="text-caption text-stone uppercase tracking-wide">Señales</p>
          {bundle.signals.map((sig, i) => (
            <div key={i} className="flex items-start gap-2">
              <span className={`w-1.5 h-1.5 rounded-full mt-1.5 flex-shrink-0 ${SEVERITY_DOT[sig.severity] ?? "bg-stone"}`} />
              <div className="min-w-0">
                <p className="text-body-sm text-on-dark font-medium">{sig.title}</p>
                <p className="text-caption text-stone">{sig.summary}</p>
              </div>
            </div>
          ))}
        </div>
      )}

      {bundle.actions.length > 0 && (
        <div className="flex flex-wrap gap-2 pt-1">
          {bundle.actions.map((act, i) => (
            <button
              key={i}
              onClick={() => navigate(act.target)}
              className="ui-pressable rounded-lg border border-hairline-dark bg-surface-elevated px-3 py-1.5 text-caption text-on-dark hover:border-primary/40"
            >
              {act.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default function AnalysisCenter({ onOpenChat }: { onOpenChat: () => void }) {
  const { briefs, generating, error, load, generate } = useBriefs();

  useEffect(() => {
    load();
  }, [load]);

  const current = briefs[0];
  const history = briefs.slice(1);

  return (
    <section className="min-h-0 flex-1 space-y-4 overflow-y-auto">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="text-heading-sm text-on-dark">Análisis mensual</h2>
          <p className="mt-1 text-sm text-stone">Un resumen trazable de lo que cambió, por qué importa y qué puedes hacer.</p>
        </div>
        {current && (
          <button
            onClick={() => generate()}
            disabled={generating}
            className="ui-pressable mercury-button inline-flex items-center gap-2 px-3 py-2 text-xs"
          >
            {generating ? <RefreshCw size={14} className="animate-spin" /> : <RefreshCw size={14} />}
            {generating ? "Actualizando…" : "Actualizar"}
          </button>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg bg-accent-danger/10 border border-accent-danger/30 px-3 py-2">
          <AlertCircle size={12} className="text-accent-danger flex-shrink-0" />
          <p className="text-caption text-accent-danger">{error}</p>
        </div>
      )}

      {generating && !current ? (
        <div className="premium-card flex min-h-56 flex-col items-center justify-center rounded-[16px] text-center">
          <RefreshCw size={22} className="animate-spin text-primary-bright" />
          <p className="mt-3 text-sm font-medium text-on-dark">Preparando tu análisis</p>
          <p className="mt-1 text-xs text-stone">Estamos ordenando cifras y señales del periodo.</p>
        </div>
      ) : current ? (
        <BriefHero brief={current} />
      ) : (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,1.35fr)_minmax(260px,.65fr)]">
            <EmptyState
              icon={Sparkles}
              title="Convierte tus cifras en decisiones"
              description="Genera una lectura mensual con cambios relevantes, señales y próximos pasos basados en datos ya calculados."
              action={
                <button
                  onClick={() => generate()}
                  className="ui-pressable mercury-button-primary inline-flex items-center gap-2"
                >
                  <Sparkles size={15} />
                  Generar análisis
                </button>
              }
              secondaryAction={
                <button onClick={onOpenChat} className="ui-pressable mercury-button">
                  Abrir chat
                </button>
              }
            />
            <aside className="premium-card rounded-[16px] p-5">
              <p className="text-sm font-semibold text-on-dark">Qué recibirás</p>
              <div className="mt-4 space-y-4">
                {[
                  ["Cambios del mes", "Ingresos, gastos, ahorro y patrimonio."],
                  ["Señales relevantes", "Desviaciones que merecen tu atención."],
                  ["Próximos pasos", "Acciones concretas enlazadas con cada módulo."],
                ].map(([title, copy], index) => (
                  <div key={title} className="flex gap-3">
                    <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-primary/10 text-xs font-semibold text-primary-bright">
                      {index + 1}
                    </span>
                    <div>
                      <p className="text-sm font-medium text-on-dark">{title}</p>
                      <p className="mt-0.5 text-xs leading-5 text-stone">{copy}</p>
                    </div>
                  </div>
                ))}
              </div>
            </aside>
        </div>
      )}

      {history.length > 0 && (
        <div className="space-y-2">
          <p className="text-caption text-stone uppercase tracking-wide">Historial</p>
          {history.map((b) => (
            <div key={b.id} className="rounded-lg bg-surface-elevated border border-hairline-dark px-4 py-3">
              <div className="flex items-center justify-between gap-3">
                <p className="text-body-sm text-on-dark">{b.bundle.headline}</p>
                <span className="text-caption text-stone flex-shrink-0">{b.period}</span>
              </div>
              <TraceBadge brief={b} />
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
