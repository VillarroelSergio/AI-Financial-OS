// apps/desktop/src/features/economy/EconomyPage.tsx
import { useState } from "react";
import { TrendingUp } from "lucide-react";
import { useEconomyMI } from "@/lib/hooks/useMarketIntelligence";
import IndicatorCard from "./components/IndicatorCard";
import RegionTabs, { type RegionTab } from "./components/RegionTabs";
import ImpactCard from "./components/ImpactCard";

function LoadingSkeleton({ isIngesting }: { isIngesting: boolean }) {
  return (
    <div className="space-y-6 animate-pulse">
      {isIngesting && (
        <div className="rounded-xl border border-primary/20 bg-primary/5 p-4 text-center">
          <p className="text-body-sm text-primary">Cargando datos de mercado…</p>
          <p className="text-caption text-stone mt-1">La ingesta se ejecuta en segundo plano al arrancar</p>
        </div>
      )}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-28 rounded-xl bg-surface-elevated border border-hairline-dark" />
        ))}
      </div>
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="h-24 rounded-xl bg-surface-elevated border border-hairline-dark" />
        ))}
      </div>
    </div>
  );
}

export default function EconomyPage() {
  const { macro, impact, ingestStatus, loading, error } = useEconomyMI();
  const [activeRegion, setActiveRegion] = useState<RegionTab>("ES");

  const isIngesting = ingestStatus?.status === "running" || ingestStatus?.status === "idle";

  const activeRegionData = macro
    ? activeRegion === "ES"
      ? macro.spain
      : activeRegion === "EA"
      ? macro.eurozone
      : macro.usa
    : [];

  const globalIndicators = macro
    ? [...macro.spain, ...macro.eurozone, ...macro.usa].slice(0, 4)
    : [];

  const generatedAt = macro?.generated_at
    ? new Date(macro.generated_at).toLocaleString("es-ES", {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      })
    : null;

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-display-lg text-on-dark">Economía</h1>
          <p className="text-body-md text-stone mt-1">
            Indicadores macroeconómicos — España, Eurozona, EEUU
          </p>
          {generatedAt && (
            <p className="text-caption text-mute mt-0.5">Actualizado: {generatedAt}</p>
          )}
        </div>
      </div>

      {loading && <LoadingSkeleton isIngesting={isIngesting} />}

      {error && !loading && (
        <div className="rounded-xl border border-accent-danger/30 bg-accent-danger/5 p-6">
          <p className="text-body-sm text-accent-danger">{error}</p>
        </div>
      )}

      {!loading && macro && (
        <>
          {globalIndicators.length > 0 && (
            <section>
              <h2 className="text-caption text-mute uppercase tracking-widest mb-3">
                Snapshot global
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {globalIndicators.map((ind) => (
                  <IndicatorCard key={ind.catalog_item_id} indicator={ind} size="large" />
                ))}
              </div>
            </section>
          )}

          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-caption text-mute uppercase tracking-widest">
                Indicadores por región
              </h2>
              <RegionTabs active={activeRegion} onSelect={setActiveRegion} />
            </div>
            {activeRegionData.length > 0 ? (
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                {activeRegionData.map((ind) => (
                  <IndicatorCard key={ind.catalog_item_id} indicator={ind} />
                ))}
              </div>
            ) : (
              <div className="rounded-xl border border-hairline-dark bg-surface-elevated p-8 text-center">
                <p className="text-stone text-body-sm">No hay datos disponibles para esta región.</p>
              </div>
            )}
          </section>

          {impact && impact.comparatives.length > 0 && (
            <section>
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp size={14} className="text-primary" />
                <h2 className="text-caption text-mute uppercase tracking-widest">
                  Impacto en tus finanzas
                </h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {impact.comparatives.map((c) => (
                  <ImpactCard key={c.id} item={c} />
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
