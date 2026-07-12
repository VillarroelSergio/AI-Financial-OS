import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Activity, RefreshCw } from "lucide-react";
import { PageHeader } from "@/components/ui/Dashboard";
import { getSparklines } from "@/lib/api/market-intelligence";
import { useMarketsMI } from "@/lib/hooks/useMarketIntelligence";
import QuoteRow from "./components/QuoteRow";
import QualityBadge from "./components/QualityBadge";

type Tab = "indices" | "commodities" | "forex" | "bonds";

function LoadingSkeleton({ isIngesting }: { isIngesting: boolean }) {
  return (
    <div className="premium-card rounded-lg overflow-hidden">
      {isIngesting && <div className="px-6 py-3 border-b border-hairline-dark bg-primary/5"><p className="text-caption text-primary-bright">Cargando datos de mercado...</p></div>}
      <div className="divide-y divide-divider-soft">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="grid grid-cols-3 items-center gap-4 px-6 py-3 animate-pulse">
            <div className="space-y-1.5"><div className="h-3.5 w-28 rounded bg-stone/20" /><div className="h-3 w-14 rounded bg-stone/20" /></div>
            <div className="h-3.5 w-20 rounded bg-stone/20 ml-auto" />
            <div className="h-5 w-16 rounded-full bg-stone/20 ml-auto" />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function MarketsPage() {
  const { market, forex, bonds, ingestStatus, loading, error, refetch } = useMarketsMI();
  const [sparklines, setSparklines] = useState<Record<string, number[]>>({});
  const [activeTab, setActiveTab] = useState<Tab>("indices");

  // MKT-8: una sola llamada batch para todas las filas con histórico (índices/cripto/commodities).
  useEffect(() => {
    const codes = [
      ...(market?.indices ?? []),
      ...(market?.crypto ?? []),
      ...(market?.commodities ?? []),
    ].map((q) => q.catalog_item_id);
    if (!codes.length) return;
    let alive = true;
    getSparklines(codes)
      .then((r) => { if (alive) setSparklines(r); })
      .catch(() => { if (alive) setSparklines({}); });
    return () => { alive = false; };
  }, [market]);
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null);
  const isIngesting = ingestStatus?.phase === "running";

  const ingestFailures = (categories: string[]) =>
    (ingestStatus?.results ?? []).filter((r) => !r.success && categories.includes(r.category));

  const EmptySection = ({ categories, fallbackText }: { categories: string[]; fallbackText: string }) => {
    const failures = ingestFailures(categories);
    return (
      <div className="p-8 text-center space-y-2">
        <p className="text-stone text-body-sm">{fallbackText}</p>
        {ingestStatus?.storage_warning && <p className="text-body-sm text-amber-200">{ingestStatus.storage_warning}</p>}
        {failures.map((f) => (
          <p key={f.indicator} className="text-caption text-stone">
            {f.indicator}: {f.error ?? "sin datos"}
          </p>
        ))}
      </div>
    );
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refetch();
      setLastRefresh(new Date());
    } finally {
      setRefreshing(false);
    }
  };
  const tabs: { key: Tab; label: string }[] = [
    { key: "indices", label: "Indices & Cripto" },
    { key: "commodities", label: "Materias primas" },
    { key: "forex", label: "Divisas" },
    { key: "bonds", label: "Bonos" },
  ];

  return (
    <div className="p-8 space-y-6 max-w-[1400px]">
      <PageHeader
        eyebrow="Market intelligence"
        title="Mercados"
        description="Terminal compacto con indices, materias primas, divisas y bonos alimentado por Market Intelligence."
        actions={
          <div className="flex items-center gap-2">
            <button
              onClick={handleRefresh}
              disabled={refreshing || loading}
              className="flex items-center gap-1.5 rounded-lg bg-white/5 px-3 py-1.5 text-xs text-stone hover:text-on-dark disabled:opacity-50 transition-colors"
            >
              <RefreshCw size={12} className={refreshing ? "animate-spin" : ""} />
              {refreshing
                ? "Actualizando..."
                : lastRefresh
                ? `Actualizado ${lastRefresh.toLocaleTimeString("es-ES")}`
                : "Actualizar"}
            </button>
            {market && !loading && (
              <QualityBadge score={market.quality_score ?? 0} generatedAt={market.generated_at} />
            )}
          </div>
        }
      />

      <section className="premium-card rounded-lg p-5">
        <div className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-lg border border-hairline-dark bg-white/[.035] text-primary-bright"><Activity size={18} /></span>
          <div>
            <p className="text-sm font-semibold text-on-dark">Pulso de mercado</p>
            <p className="text-xs text-stone">Vista densa para seguimiento diario y validacion de calidad de dato.</p>
          </div>
        </div>
      </section>

      <div className="flex w-fit gap-1 rounded-lg border border-hairline-dark bg-white/[.035] p-1">
        {tabs.map((tab) => (
          <button key={tab.key} onClick={() => setActiveTab(tab.key)} className={["rounded-lg px-4 py-2 text-body-sm transition-colors", activeTab === tab.key ? "bg-white/[.08] text-on-dark shadow-[inset_0_0_0_1px_rgba(255,255,255,.08)]" : "text-stone hover:text-on-dark"].join(" ")}>
            {tab.label}
          </button>
        ))}
      </div>

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
      {error && !loading && <div className="rounded-lg border border-accent-danger/30 bg-accent-danger/5 p-6"><p className="text-body-sm text-accent-danger">{error}</p></div>}
      {market?.warnings?.length ? (
        <div className="rounded-lg border border-amber-400/25 bg-amber-400/10 p-4">
          <p className="text-body-sm text-amber-200">{market.warnings[0]}</p>
          <p className="text-caption text-stone mt-1">Actualizado: {new Date(market.generated_at).toLocaleString("es-ES")} · Estado: {market.status}</p>
        </div>
      ) : null}

      {!loading && activeTab === "indices" && (
        <div className="premium-card rounded-lg overflow-hidden">
          {market && market.indices.length > 0 && (
            <>
              <div className="px-6 pt-4 pb-2"><span className="text-caption text-mute uppercase tracking-widest font-medium">Indices</span></div>
              <div className="divide-y divide-divider-soft">{market.indices.map((q) => <QuoteRow key={q.catalog_item_id} quote={q} sparkline={sparklines[q.catalog_item_id]} />)}</div>
            </>
          )}
          {market && market.crypto.length > 0 && (
            <>
              <div className="border-t border-hairline-dark px-6 pt-4 pb-2"><span className="text-caption text-mute uppercase tracking-widest font-medium">Criptomonedas</span></div>
              <div className="divide-y divide-divider-soft">{market.crypto.map((q) => <QuoteRow key={q.catalog_item_id} quote={q} sparkline={sparklines[q.catalog_item_id]} />)}</div>
            </>
          )}
          {(!market || (market.indices.length === 0 && market.crypto.length === 0)) && (
            <EmptySection categories={["indices", "crypto"]} fallbackText="Sin datos de indices o cripto. La ingesta no ha devuelto esas secciones." />
          )}
        </div>
      )}

      {!loading && activeTab === "commodities" && (
        <div className="premium-card rounded-lg overflow-hidden">
          {market && market.commodities.length > 0 ? <div className="divide-y divide-divider-soft">{market.commodities.map((q) => <QuoteRow key={q.catalog_item_id} quote={q} sparkline={sparklines[q.catalog_item_id]} />)}</div> : <EmptySection categories={["commodities"]} fallbackText="Sin datos de materias primas disponibles." />}
        </div>
      )}

      {!loading && activeTab === "forex" && (
        <div className="premium-card rounded-lg overflow-hidden">
          {forex && forex.rates.length > 0 ? (
            <div className="divide-y divide-divider-soft">
              {forex.rates.map((r) => (
                <Link key={r.catalog_item_id} to={`/markets/${encodeURIComponent(r.catalog_item_id)}`} className="grid grid-cols-[1fr_120px_100px] items-center gap-4 px-6 py-3 hover:bg-white/[.03] transition-colors">
                  <div>
                    <p className="text-body-sm text-on-dark">{r.base_currency ?? "-"} / {r.quote_currency ?? "-"}</p>
                  </div>
                  <p className="text-body-sm font-semibold text-on-dark tabular-nums text-right">{r.rate != null ? r.rate.toLocaleString("es-ES", { minimumFractionDigits: 4, maximumFractionDigits: 4 }) : "-"}</p>
                  <p className="text-caption text-stone text-right">{r.date ?? "-"}</p>
                </Link>
              ))}
            </div>
          ) : <div className="p-8 text-center"><p className="text-stone text-body-sm">Sin datos de divisas. No se mezclan bonos ni macro en esta seccion.</p></div>}
        </div>
      )}

      {!loading && activeTab === "bonds" && (
        <div className="premium-card rounded-lg overflow-hidden">
          {bonds && bonds.yields.length > 0 ? (
            <div className="divide-y divide-divider-soft">
              {bonds.yields.map((b) => (
                <div key={b.catalog_item_id} className="grid grid-cols-[1fr_120px_100px] items-center gap-4 px-6 py-3">
                  <div>
                    <p className="text-body-sm text-on-dark">{b.country ?? "-"} {b.maturity ?? ""}</p>
                  </div>
                  <p className="text-body-sm font-semibold text-on-dark tabular-nums text-right">{b.yield_value != null ? `${b.yield_value.toLocaleString("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%` : "-"}</p>
                  <p className="text-caption text-stone text-right">{b.date ?? "-"}</p>
                </div>
              ))}
            </div>
          ) : <div className="p-8 text-center"><p className="text-stone text-body-sm">Sin datos de bonos. Se mostraran aqui cuando Market Intelligence tenga yields disponibles.</p></div>}
        </div>
      )}
    </div>
  );
}
