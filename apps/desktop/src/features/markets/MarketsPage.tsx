import { useState } from "react";
import type { MarketCategory } from "@/lib/types";
import { useMarkets } from "@/lib/hooks/useMarkets";
import CategoryTabs from "./components/CategoryTabs";
import LiveIndicator from "./components/LiveIndicator";
import QuoteRow from "./components/QuoteRow";

const CATEGORY_ORDER: Array<{ key: MarketCategory; label: string }> = [
  { key: "indices_eu", label: "EUROPA" },
  { key: "indices_us", label: "ESTADOS UNIDOS" },
  { key: "indices_asia", label: "ASIA" },
  { key: "crypto", label: "CRIPTOMONEDAS" },
  { key: "fx", label: "DIVISAS" },
  { key: "bonds", label: "BONOS 10Y" },
  { key: "commodities", label: "MATERIAS PRIMAS" },
  { key: "volatility", label: "VOLATILIDAD" },
];

export default function MarketsPage() {
  const [activeCategory, setActiveCategory] = useState<MarketCategory | "all">("all");
  const { quotes, loading, error, secondsSinceUpdate } = useMarkets(
    activeCategory === "all" ? undefined : activeCategory
  );

  return (
    <div className="p-xxxl space-y-xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-heading-lg text-on-dark">Mercados</h1>
        <LiveIndicator secondsSinceUpdate={secondsSinceUpdate} />
      </div>

      {/* Category tabs */}
      <CategoryTabs activeCategory={activeCategory} onSelect={setActiveCategory} />

      {/* Loading skeleton */}
      {loading && (
        <div className="rounded-lg border border-hairline-dark bg-surface-elevated divide-y divide-divider-soft">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4 px-6 py-3 animate-pulse">
              <div className="flex-1 space-y-1">
                <div className="h-3.5 w-32 rounded bg-stone/20" />
                <div className="h-3 w-16 rounded bg-stone/20" />
              </div>
              <div className="w-[60px] h-6 rounded bg-stone/20" />
              <div className="h-4 w-20 rounded bg-stone/20" />
              <div className="h-5 w-16 rounded-full bg-stone/20" />
            </div>
          ))}
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div className="rounded-lg border border-red-500 bg-surface-elevated p-xl">
          <p className="text-body-md-bold text-on-dark">Error al cargar datos de mercado</p>
          <p className="text-body-sm text-stone mt-1">{error}</p>
        </div>
      )}

      {/* All categories grouped */}
      {!loading && !error && activeCategory === "all" && (
        <div className="rounded-lg border border-hairline-dark bg-surface-elevated overflow-hidden">
          {CATEGORY_ORDER.map((cat, catIdx) => {
            const catQuotes = quotes.filter((q) => q.category === cat.key);
            if (!catQuotes.length) return null;
            return (
              <div key={cat.key}>
                {catIdx > 0 && <div className="border-t border-divider-soft" />}
                <div className="px-6 pt-4 pb-1">
                  <span className="text-caption text-stone uppercase tracking-widest">
                    {cat.label}
                  </span>
                </div>
                <div className="divide-y divide-divider-soft">
                  {catQuotes.map((q) => (
                    <QuoteRow key={q.symbol} quote={q} />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Single category flat list */}
      {!loading && !error && activeCategory !== "all" && (
        <div className="rounded-lg border border-hairline-dark bg-surface-elevated overflow-hidden divide-y divide-divider-soft">
          {quotes.map((q) => (
            <QuoteRow key={q.symbol} quote={q} />
          ))}
        </div>
      )}
    </div>
  );
}
