// apps/desktop/src/features/markets/MarketsPage.tsx
import { useState } from "react";
import { useMarketsMI } from "@/lib/hooks/useMarketIntelligence";
import QuoteRow from "./components/QuoteRow";
import QualityBadge from "./components/QualityBadge";

type Tab = "indices" | "forex" | "bonds";


function LoadingSkeleton({ isIngesting }: { isIngesting: boolean }) {
  return (
    <div className="rounded-lg border border-hairline-dark bg-surface-elevated overflow-hidden">
      {isIngesting && (
        <div className="px-6 py-3 border-b border-hairline-dark bg-primary/5">
          <p className="text-caption text-primary">Cargando datos de mercado…</p>
        </div>
      )}
      <div className="divide-y divide-divider-soft">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="grid grid-cols-3 items-center gap-4 px-6 py-3 animate-pulse">
            <div className="space-y-1.5">
              <div className="h-3.5 w-28 rounded bg-stone/20" />
              <div className="h-3 w-14 rounded bg-stone/20" />
            </div>
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

  const avgQuality = market
    ? [...market.indices, ...market.crypto].reduce((s, q) => s + q.quality_score, 0) /
      Math.max([...market.indices, ...market.crypto].length, 1)
    : 0;

  const tabs: { key: Tab; label: string }[] = [
    { key: "indices", label: "Índices & Cripto" },
    { key: "forex", label: "Divisas" },
    { key: "bonds", label: "Bonos" },
  ];

  return (
    <div className="p-8 space-y-6 max-w-[1400px]">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-heading-md text-on-dark">Mercados</h1>
          <p className="text-caption text-stone mt-1">
            Datos de mercado en tiempo real desde Market Intelligence.
          </p>
        </div>
        {market && !loading && (
          <QualityBadge score={avgQuality} generatedAt={market.generated_at} />
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 border-b border-hairline-dark">
        {tabs.map((t) => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={[
              "px-4 py-2 text-body-sm transition-colors border-b-2 -mb-px",
              activeTab === t.key
                ? "border-primary text-on-dark"
                : "border-transparent text-stone hover:text-on-dark",
            ].join(" ")}
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading && <LoadingSkeleton isIngesting={isIngesting} />}

      {error && !loading && (
        <div className="rounded-lg border border-accent-danger/30 bg-accent-danger/5 p-6">
          <p className="text-body-sm text-accent-danger">{error}</p>
        </div>
      )}

      {!loading && activeTab === "indices" && (
        <div className="rounded-lg border border-hairline-dark bg-surface-elevated overflow-hidden">
          {market && market.indices.length > 0 && (
            <>
              <div className="px-6 pt-4 pb-2">
                <span className="text-caption text-mute uppercase tracking-widest font-medium">Índices</span>
              </div>
              <div className="divide-y divide-divider-soft">
                {market.indices.map((q) => <QuoteRow key={q.catalog_item_id} quote={q} />)}
              </div>
            </>
          )}
          {market && market.crypto.length > 0 && (
            <>
              <div className="border-t border-hairline-dark px-6 pt-4 pb-2">
                <span className="text-caption text-mute uppercase tracking-widest font-medium">Criptomonedas</span>
              </div>
              <div className="divide-y divide-divider-soft">
                {market.crypto.map((q) => <QuoteRow key={q.catalog_item_id} quote={q} />)}
              </div>
            </>
          )}
          {(!market || (market.indices.length === 0 && market.crypto.length === 0)) && (
            <div className="p-8 text-center">
              <p className="text-stone text-body-sm">Sin datos de índices. La ingesta está en curso.</p>
            </div>
          )}
        </div>
      )}

      {!loading && activeTab === "forex" && (
        <div className="rounded-lg border border-hairline-dark bg-surface-elevated overflow-hidden">
          {forex && forex.rates.length > 0 ? (
            <div className="divide-y divide-divider-soft">
              {forex.rates.map((r) => (
                <div key={r.catalog_item_id} className="grid grid-cols-[1fr_120px_80px] items-center gap-4 px-6 py-3">
                  <div>
                    <p className="text-body-sm text-on-dark">{r.base_currency ?? "—"} / {r.quote_currency ?? "—"}</p>
                    <p className="text-caption text-stone">{r.catalog_item_id}</p>
                  </div>
                  <p className="text-body-sm font-semibold text-on-dark tabular-nums text-right">
                    {r.rate != null ? r.rate.toLocaleString("es-ES", { minimumFractionDigits: 4, maximumFractionDigits: 4 }) : "—"}
                  </p>
                  <p className="text-caption text-stone text-right">{r.date ?? "—"}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center">
              <p className="text-stone text-body-sm">Sin datos de divisas. La ingesta está en curso.</p>
            </div>
          )}
        </div>
      )}

      {!loading && activeTab === "bonds" && (
        <div className="rounded-lg border border-hairline-dark bg-surface-elevated overflow-hidden">
          {bonds && bonds.yields.length > 0 ? (
            <div className="divide-y divide-divider-soft">
              {bonds.yields.map((b) => (
                <div key={b.catalog_item_id} className="grid grid-cols-[1fr_120px_80px] items-center gap-4 px-6 py-3">
                  <div>
                    <p className="text-body-sm text-on-dark">{b.country ?? "—"} {b.maturity ?? ""}</p>
                    <p className="text-caption text-stone">{b.catalog_item_id}</p>
                  </div>
                  <p className="text-body-sm font-semibold text-on-dark tabular-nums text-right">
                    {b.yield_value != null
                      ? `${b.yield_value.toLocaleString("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}%`
                      : "—"}
                  </p>
                  <p className="text-caption text-stone text-right">{b.date ?? "—"}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-8 text-center">
              <p className="text-stone text-body-sm">Sin datos de bonos. La ingesta está en curso.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
