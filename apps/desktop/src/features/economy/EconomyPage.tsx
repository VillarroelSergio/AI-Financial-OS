import { useState } from "react";
import { TrendingUp } from "lucide-react";
import { ErrorState, PageHeader } from "@/components/ui/Dashboard";
import { useEconomyMI } from "@/lib/hooks/useMarketIntelligence";
import IndicatorCard from "./components/IndicatorCard";
import RegionTabs, { type RegionTab } from "./components/RegionTabs";
import ImpactCard from "./components/ImpactCard";

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
  const { macro, impact, ingestStatus, loading, error } = useEconomyMI();
  const [activeRegion, setActiveRegion] = useState<RegionTab>("ES");

  const isIngesting = ingestStatus?.status === "running" || ingestStatus?.status === "idle";
  const activeRegionData = macro ? activeRegion === "ES" ? macro.spain : activeRegion === "EA" ? macro.eurozone : macro.usa : [];
  const globalIndicators = macro ? [...macro.spain, ...macro.eurozone, ...macro.usa].slice(0, 4) : [];
  const generatedAt = macro?.generated_at
    ? new Date(macro.generated_at).toLocaleString("es-ES", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" })
    : null;

  return (
    <div className="p-8 space-y-8 max-w-[1500px] mx-auto">
      <PageHeader
        eyebrow="Contexto macro"
        title="Economia"
        description="Indicadores macroeconomicos agrupados por Espana, Eurozona y EEUU con impacto personal cuando hay datos suficientes."
        actions={<span className="rounded-lg border border-hairline-dark bg-white/[.035] px-3 py-2 text-xs text-stone">{generatedAt ? `Actualizado ${generatedAt}` : "Dato en cache"}</span>}
      />

      {loading && <LoadingSkeleton isIngesting={isIngesting} />}

      {error && !loading && (
        <ErrorState
          title="No se han podido actualizar los datos macro"
          description="Mostramos el ultimo estado disponible. Reintenta cuando Market Intelligence este activo."
        />
      )}

      {!loading && macro && (
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

          <section className="premium-card rounded-lg p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-caption text-mute uppercase tracking-widest">Indicadores por region</h2>
              <RegionTabs active={activeRegion} onSelect={setActiveRegion} />
            </div>
            {activeRegionData.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {activeRegionData.map((ind) => <IndicatorCard key={ind.catalog_item_id} indicator={ind} />)}
              </div>
            ) : (
              <div className="rounded-lg border border-hairline-dark bg-white/[.035] p-8 text-center">
                <p className="text-stone text-body-sm">No hay datos disponibles para esta region.</p>
              </div>
            )}
          </section>

          {impact && impact.comparatives.length > 0 && (
            <section>
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp size={14} className="text-primary-bright" />
                <h2 className="text-caption text-mute uppercase tracking-widest">Impacto en tus finanzas</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {impact.comparatives.map((c) => <ImpactCard key={c.id} item={c} />)}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
