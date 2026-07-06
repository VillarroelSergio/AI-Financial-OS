import { useState, useEffect, useMemo } from "react";
import { TrendingUp, ChevronDown } from "lucide-react";
import { ErrorState, PageHeader } from "@/components/ui/Dashboard";
import { useEconomyMI } from "@/lib/hooks/useMarketIntelligence";
import type { ImpactComparative, MacroDataPointMI } from "@/lib/types/market-intelligence";
import IndicatorCard from "./components/IndicatorCard";
import RegionTabs, { type RegionTab } from "./components/RegionTabs";
import ImpactCard from "./components/ImpactCard";
import PersonalEconomySection from "./components/PersonalEconomySection";
import RatesAndDebtSection from "./components/RatesAndDebtSection";

// ECO-6: la agrupación temática y el snapshot global ahora los resuelve el backend
// (GET economy/overview). Aquí solo queda el orden de severidad de comparativas.
const SIGNAL_RANK: Record<ImpactComparative["signal"], number> = {
  negative: 0,
  warning: 1,
  positive: 2,
  neutral: 3,
  no_data: 4,
};

function LoadingSkeleton({ isIngesting }: { isIngesting: boolean }) {
  return (
    <div className="space-y-6 animate-pulse">
      {isIngesting && (
        <div className="rounded-lg border border-primary/20 bg-primary/5 p-4 text-center">
          <p className="text-body-sm text-primary-bright">Cargando datos de mercado...</p>
          <p className="text-caption text-stone mt-1">La ingesta se ejecuta en segundo plano al arrancar</p>
        </div>
      )}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {Array.from({ length: 4 }).map((_, i) => <div key={i} className="h-28 rounded-lg bg-surface-elevated border border-hairline-dark" />)}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {Array.from({ length: 6 }).map((_, i) => <div key={i} className="h-24 rounded-lg bg-surface-elevated border border-hairline-dark" />)}
      </div>
    </div>
  );
}

export default function EconomyPage() {
  const { overview, ingestStatus, loading, error } = useEconomyMI();
  const [activeRegion, setActiveRegion] = useState<RegionTab>("ES");
  const [showSecondary, setShowSecondary] = useState(false);

  const regions = overview?.regions ?? {};
  const availableRegions = (["ES", "EA", "US"] as RegionTab[]).filter(
    (r) => (regions[r]?.themes.length ?? 0) > 0
  );

  useEffect(() => {
    if (availableRegions.length > 0 && !availableRegions.includes(activeRegion)) {
      setActiveRegion(availableRegions[0]);
    }
  }, [availableRegions]);

  useEffect(() => setShowSecondary(false), [activeRegion]);

  const isIngesting = ingestStatus?.phase === "running";
  const activeThemes = regions[activeRegion]?.themes ?? [];
  const activeIndicators = activeThemes.flatMap((t) => t.indicators);

  // EEUU a mínimos: solo indicadores críticos por defecto; el resto tras "mostrar más".
  const visiblePriorities = activeRegion === "US" ? ["critical"] : ["critical", "high"];
  const isPrimary = (i: MacroDataPointMI) => visiblePriorities.includes(i.priority ?? "medium");
  const secondary = activeIndicators.filter((i) => !isPrimary(i));
  const hasPrimary = activeIndicators.some(isPrimary);

  // El backend ya agrupó por tema; aquí solo filtramos por prioridad para el "mostrar más".
  const themedGroups = useMemo(
    () =>
      activeThemes
        .map((t): [string, MacroDataPointMI[]] => [
          t.theme,
          showSecondary || !hasPrimary ? t.indicators : t.indicators.filter(isPrimary),
        ])
        .filter(([, inds]) => inds.length > 0),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [activeThemes, showSecondary, hasPrimary, activeRegion]
  );

  const globalIndicators = overview?.global_indicators ?? [];
  const spainIndicators = (regions.ES?.themes ?? []).flatMap((t) => t.indicators);

  const generatedAt = overview?.generated_at
    ? new Date(overview.generated_at).toLocaleString("es-ES", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })
    : null;

  const comparatives = overview?.impact.comparatives ?? [];
  const withData = comparatives
    .filter((c) => c.signal !== "no_data")
    .sort((a, b) => SIGNAL_RANK[a.signal] - SIGNAL_RANK[b.signal]);
  const noData = comparatives.filter((c) => c.signal === "no_data");

  return (
    <div className="p-8 space-y-8 max-w-[1500px] mx-auto">
      <PageHeader
        eyebrow="Contexto macro"
        title="Economia"
        description="Indicadores macroeconomicos agrupados por Espana, Eurozona y EEUU con impacto personal cuando hay datos suficientes."
        actions={<span className="rounded-lg border border-hairline-dark bg-white/[.035] px-3 py-2 text-xs text-stone">{generatedAt ? `Actualizado ${generatedAt}` : "Dato en cache"}</span>}
      />

      {ingestStatus?.last_run_at && (
        <p className="text-caption text-stone">
          Datos actualizados: {new Date(ingestStatus.last_run_at).toLocaleString("es-ES", {
            day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
          })}
        </p>
      )}

      {loading && <LoadingSkeleton isIngesting={isIngesting} />}

      {!loading && isIngesting && (
        <div className="rounded-lg border border-primary/20 bg-primary/5 px-4 py-2.5">
          <p className="text-caption text-primary-bright">Actualizando datos en segundo plano… Se muestran los ultimos datos disponibles.</p>
        </div>
      )}

      {ingestStatus?.storage_warning && (
        <div className="rounded-lg border border-amber-400/25 bg-amber-400/10 px-4 py-2.5">
          <p className="text-caption text-amber-200">{ingestStatus.storage_warning}</p>
        </div>
      )}

      {error && !loading && (
        <ErrorState
          title="No se han podido actualizar los datos macro"
          description="Mostramos el ultimo estado disponible. Reintenta cuando Market Intelligence este activo."
        />
      )}

      {!loading && overview && (
        <>
          {globalIndicators.length > 0 && (
            <section className="space-y-3">
              <div className="flex items-center justify-between">
                <h2 className="text-caption text-mute uppercase tracking-widest">Snapshot global</h2>
                <span className="rounded-lg bg-primary/10 px-2.5 py-1 text-[11px] text-primary-bright">Fuente cacheada</span>
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {globalIndicators.map((ind) => <IndicatorCard key={ind.catalog_item_id} indicator={ind} size="large" />)}
              </div>
            </section>
          )}

          <PersonalEconomySection data={overview.personal_economy} macroSpain={spainIndicators} />

          <RatesAndDebtSection bonds={overview.bonds} forex={overview.forex} />

          <section className="premium-card rounded-lg p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-caption text-mute uppercase tracking-widest">Indicadores por region</h2>
              <RegionTabs active={activeRegion} onSelect={setActiveRegion} availableRegions={availableRegions} />
            </div>
            {activeIndicators.length > 0 ? (
              <div className="space-y-5">
                {themedGroups.map(([theme, indicators]) => (
                  <div key={theme} className="space-y-2">
                    <h3 className="text-[11px] text-stone uppercase tracking-wider">{theme}</h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                      {indicators.map((ind) => <IndicatorCard key={ind.catalog_item_id} indicator={ind} />)}
                    </div>
                  </div>
                ))}
                {secondary.length > 0 && (
                  <button
                    type="button"
                    onClick={() => setShowSecondary((v) => !v)}
                    className="flex items-center gap-1.5 text-caption text-primary-bright hover:underline"
                  >
                    <ChevronDown size={12} className={showSecondary ? "rotate-180 transition-transform" : "transition-transform"} />
                    {showSecondary ? "Mostrar menos" : `Mostrar ${secondary.length} indicadores más`}
                  </button>
                )}
              </div>
            ) : (
              <div className="rounded-lg border border-hairline-dark bg-white/[.035] p-8 text-center">
                <p className="text-stone text-body-sm">No hay datos disponibles para esta region.</p>
              </div>
            )}
          </section>

          {comparatives.length > 0 && (
            <section className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <TrendingUp size={14} className="text-primary-bright" />
                  <h2 className="text-caption text-mute uppercase tracking-widest">Impacto en tus finanzas</h2>
                </div>
                <span className="text-[11px] text-mute">
                  {withData.length} de {comparatives.length} comparativas con datos
                </span>
              </div>

              {withData.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {withData.map((c) => <ImpactCard key={c.id} item={c} />)}
                </div>
              ) : (
                <div className="rounded-lg border border-hairline-dark bg-white/[.035] p-6 text-center">
                  <p className="text-stone text-body-sm">
                    Sin datos de mercado suficientes para calcular el impacto personal.
                  </p>
                </div>
              )}

              {noData.length > 0 && (
                <details className="rounded-lg border border-hairline-dark bg-white/[.02]">
                  <summary className="cursor-pointer select-none px-4 py-3 text-caption text-stone">
                    Sin datos de mercado ({noData.length})
                  </summary>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 p-4 pt-1">
                    {noData.map((c) => <ImpactCard key={c.id} item={c} />)}
                  </div>
                </details>
              )}
            </section>
          )}
        </>
      )}
    </div>
  );
}
