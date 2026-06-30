import { useState } from "react";
import { Activity } from "lucide-react";
import { PageHeader } from "@/components/ui/Dashboard";
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
  const { market, forex, bonds, ingestStatus, loading, error } = useMarketsMI();
  const [activeTab, setActiveTab] = useState<Tab>("indices");
  const isIngesting = ingestStatus?.status === "running" || ingestStatus?.status === "idle";
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
        actions={market && !loading ? <QualityBadge score={market.quality_score ?? 0} generatedAt={market.generated_at} /> : undefined}
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
              <div className="divide-y divide-divider-soft">{market.indices.map((q) => <QuoteRow key={q.catalog_item_id} quote={q} />)}</div>
            </>
          )}
          {market && market.crypto.length > 0 && (
            <>
              <div className="border-t border-hairline-dark px-6 pt-4 pb-2"><span className="text-caption text-mute uppercase tracking-widest font-medium">Criptomonedas</span></div>
              <div className="divide-y divide-divider-soft">{market.crypto.map((q) => <QuoteRow key={q.catalog_item_id} quote={q} />)}</div>
            </>
          )}
          {(!market || (market.indices.length === 0 && market.crypto.length === 0)) && <div className="p-8 text-center"><p className="text-stone text-body-sm">Sin datos de indices o cripto. La ingesta no ha devuelto esas secciones.</p></div>}
        </div>
      )}

      {!loading && activeTab === "commodities" && (
        <div className="premium-card rounded-lg overflow-hidden">
          {market && market.commodities.length > 0 ? <div className="divide-y divide-divider-soft">{market.commodities.map((q) => <QuoteRow key={q.catalog_item_id} quote={q} />)}</div> : <div className="p-8 text-center"><p className="text-stone text-body-sm">Sin datos de materias primas disponibles.</p></div>}
        </div>
      )}

      {!loading && activeTab === "forex" && (
        <div className="premium-card rounded-lg overflow-hidden">
          {forex && forex.rates.length > 0 ? (
            <div className="divide-y divide-divider-soft">
              {forex.rates.map((r) => (
                <div key={r.catalog_item_id} className="grid grid-cols-[1fr_120px_100px] items-center gap-4 px-6 py-3">
                  <div>
                    <p className="text-body-sm text-on-dark">{r.base_currency ?? "-"} / {r.quote_currency ?? "-"}</p>
                    <p className="text-caption text-stone">{r.catalog_item_id} · {r.provider_id ?? "provider desconocido"} · calidad {(r.quality_score * 100).toFixed(0)}%</p>
                  </div>
                  <p className="text-body-sm font-semibold text-on-dark tabular-nums text-right">{r.rate != null ? r.rate.toLocaleString("es-ES", { minimumFractionDigits: 4, maximumFractionDigits: 4 }) : "-"}</p>
                  <p className="text-caption text-stone text-right">{r.date ?? "-"}</p>
                </div>
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
                    <p className="text-caption text-stone">{b.catalog_item_id} · {b.provider_id ?? "provider desconocido"} · calidad {(b.quality_score * 100).toFixed(0)}%</p>
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
