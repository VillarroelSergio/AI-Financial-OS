import { useState } from "react";
import { RefreshCw, TrendingUp } from "lucide-react";
import { useEconomy } from "@/lib/hooks/useEconomy";
import IndicatorCard from "./components/IndicatorCard";
import RegionTabs, { type RegionTab } from "./components/RegionTabs";
import ImpactCard from "./components/ImpactCard";
import type { EconomicIndicator, RegionSnapshot } from "@/lib/types";
import { ErrorState as PremiumErrorState } from "@/components/ui/Dashboard";

// Indicators shown in the top global snapshot strip
const GLOBAL_SERIES = ["ESPCPIALLMINMEI", "ECBDFR", "FEDFUNDS", "EURUSD"];

function LoadingSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
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

function RegionGrid({ regionData }: { regionData: RegionSnapshot }) {
  if (!regionData.indicators.length) {
    return (
      <div className="rounded-xl border border-hairline-dark bg-surface-elevated p-8 text-center">
        <p className="text-stone text-body-sm">No hay datos disponibles para esta región.</p>
        <p className="text-mute text-caption mt-1">Configura FRED_API_KEY en tu archivo .env</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
      {regionData.indicators.map((ind) => (
        <IndicatorCard key={ind.series_id} indicator={ind} />
      ))}
    </div>
  );
}

export default function EconomyPage() {
  const { snapshot, impact, loading, error, refreshing, refresh } = useEconomy();
  const [activeRegion, setActiveRegion] = useState<RegionTab>("ES");

  const allIndicators: EconomicIndicator[] = snapshot
    ? [
        ...snapshot.spain.indicators,
        ...snapshot.eurozone.indicators,
        ...snapshot.us.indicators,
      ]
    : [];

  const globalIndicators = GLOBAL_SERIES
    .map((id) => allIndicators.find((i) => i.series_id === id))
    .filter(Boolean) as EconomicIndicator[];

  const activeRegionData = snapshot
    ? activeRegion === "ES"
      ? snapshot.spain
      : activeRegion === "EA"
      ? snapshot.eurozone
      : snapshot.us
    : null;

  const lastRefreshed = snapshot?.last_refreshed
    ? new Date(snapshot.last_refreshed).toLocaleString("es-ES", {
        day: "2-digit",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      })
    : null;

  return (
    <div className="p-6 md:p-8 space-y-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-display-lg text-on-dark">Economía</h1>
          <p className="text-body-md text-stone mt-1">
            Indicadores macroeconómicos — España, Eurozona, EEUU
          </p>
          {lastRefreshed && (
            <p className="text-caption text-mute mt-0.5">Actualizado: {lastRefreshed}</p>
          )}
        </div>
        <button
          onClick={refresh}
          disabled={refreshing || loading}
          aria-label="Actualizar datos económicos"
          className={[
            "flex items-center gap-2 px-4 py-2 rounded-lg text-button-sm transition-all",
            "bg-surface-elevated border border-hairline-dark text-stone",
            "hover:text-on-dark hover:border-primary/40 disabled:opacity-40 disabled:cursor-not-allowed",
          ].join(" ")}
        >
          <RefreshCw
            size={14}
            className={refreshing ? "animate-spin" : ""}
          />
          {refreshing ? "Actualizando…" : "Actualizar"}
        </button>
      </div>

      {loading && <LoadingSkeleton />}
      {error && !loading && (
        <PremiumErrorState
          title="No se han podido cargar los indicadores macroeconómicos"
          description="El proveedor local no devolvió datos para Economía. Puedes reintentar o revisar la configuración."
          onRetry={refresh}
        />
      )}

      {!loading && snapshot && (
        <>
          {/* Global snapshot strip */}
          {globalIndicators.length > 0 && (
            <section>
              <h2 className="text-caption text-mute uppercase tracking-widest mb-3">
                Snapshot global
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {globalIndicators.map((ind) => (
                  <IndicatorCard key={ind.series_id} indicator={ind} size="large" />
                ))}
              </div>
            </section>
          )}

          {/* Region tabs */}
          <section>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-caption text-mute uppercase tracking-widest">
                Indicadores por región
              </h2>
              <RegionTabs active={activeRegion} onSelect={setActiveRegion} />
            </div>
            {activeRegionData && <RegionGrid regionData={activeRegionData} />}
          </section>

          {/* Personal impact */}
          {impact && (
            <section>
              <div className="flex items-center gap-2 mb-4">
                <TrendingUp size={14} className="text-primary" />
                <h2 className="text-caption text-mute uppercase tracking-widest">
                  Impacto en tus finanzas
                </h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <ImpactCard item={impact.inflation_vs_savings} />
                <ImpactCard item={impact.rates_vs_liquidity} />
                <ImpactCard item={impact.market_vs_portfolio} />
                <ImpactCard item={impact.purchasing_power} />
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
