import { useMemo, useState } from "react";
import { RefreshCw } from "lucide-react";
import type { FreshnessStatus, MarketCategory, MarketQuote } from "@/lib/types";
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

function TableHeader() {
  return (
    <div className="grid grid-cols-[1fr_80px_120px_100px] items-center gap-4 px-6 py-2 border-b border-divider-soft">
      <span className="text-caption text-mute uppercase tracking-widest">Activo</span>
      <span className="text-caption text-mute uppercase tracking-widest text-center">Tendencia</span>
      <span className="text-caption text-mute uppercase tracking-widest text-right">Último precio</span>
      <span className="text-caption text-mute uppercase tracking-widest text-right">Cambio</span>
    </div>
  );
}

function LoadingSkeleton() {
  return (
    <div className="rounded-lg border border-hairline-dark bg-surface-elevated overflow-hidden">
      <TableHeader />
      <div className="divide-y divide-divider-soft">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="grid grid-cols-[1fr_80px_120px_100px] items-center gap-4 px-6 py-3 animate-pulse">
            <div className="space-y-1.5">
              <div className="h-3.5 w-28 rounded bg-stone/20" />
              <div className="h-3 w-14 rounded bg-stone/20" />
            </div>
            <div className="h-6 w-[60px] rounded bg-stone/20 mx-auto" />
            <div className="space-y-1.5 items-end flex flex-col">
              <div className="h-3.5 w-20 rounded bg-stone/20" />
              <div className="h-3 w-10 rounded bg-stone/20" />
            </div>
            <div className="flex flex-col items-end gap-1">
              <div className="h-5 w-16 rounded-full bg-stone/20" />
              <div className="h-3 w-14 rounded bg-stone/20" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-accent-danger/30 bg-accent-danger/5 p-6 flex items-start gap-4">
      <div className="w-8 h-8 rounded-full bg-accent-danger/15 flex items-center justify-center flex-shrink-0 mt-0.5">
        <span className="text-accent-danger text-sm font-bold">!</span>
      </div>
      <div>
        <p className="text-body-sm font-medium text-on-dark">Error al cargar datos de mercado</p>
        <p className="text-caption text-stone mt-1">{message}</p>
      </div>
    </div>
  );
}

function EmptyState({ noData }: { noData?: boolean }) {
  return (
    <div className="rounded-lg border border-hairline-dark bg-surface-elevated p-12 flex flex-col items-center text-center gap-3">
      <div className="w-10 h-10 rounded-full bg-surface-card flex items-center justify-center">
        <span className="text-stone text-lg">—</span>
      </div>
      <p className="text-body-sm text-stone">
        {noData
          ? "Pulsa «Actualizar» para cargar los datos de mercado"
          : "No hay activos disponibles para esta categoría"}
      </p>
    </div>
  );
}

interface QuotesPanelProps {
  quotes: MarketQuote[];
  selectedSymbol: string | null;
  onSelect: (symbol: string) => void;
}

function QuoteGroupPanel({ quotes, selectedSymbol, onSelect }: QuotesPanelProps) {
  return (
    <div className="rounded-lg border border-hairline-dark bg-surface-elevated overflow-hidden">
      <TableHeader />
      <div className="divide-y divide-divider-soft">
        {quotes.map((q) => (
          <QuoteRow
            key={q.symbol}
            quote={q}
            isSelected={selectedSymbol === q.symbol}
            onSelect={onSelect}
          />
        ))}
      </div>
    </div>
  );
}

export default function MarketsPage() {
  const initialCategory = new URLSearchParams(window.location.search).get("category") as MarketCategory | null;
  const [activeCategory, setActiveCategory] = useState<MarketCategory | "all">(initialCategory ?? "all");
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);
  const { quotes, loading, error, secondsSinceUpdate, refreshing, refresh } = useMarkets();

  // Client-side category filter — no extra fetches needed when switching tabs.
  const visibleQuotes = activeCategory === "all"
    ? quotes
    : quotes.filter((q) => q.category === activeCategory);

  // TODO: open asset detail panel when selectedSymbol is set
  const handleSelectAsset = (symbol: string) => {
    setSelectedSymbol((prev) => (prev === symbol ? null : symbol));
  };

  const hasData = !loading && !error && visibleQuotes.length > 0;
  const isEmpty = !loading && !error && visibleQuotes.length === 0;
  const isInitial = isEmpty && quotes.length === 0;

  // Compute worst freshness across all loaded quotes to drive LiveIndicator
  const freshnessStatus = useMemo<FreshnessStatus>(() => {
    if (!quotes.length) return "unknown";
    const priority: FreshnessStatus[] = [
      "error", "stale", "unknown", "closed", "eod", "delayed", "fresh", "live",
    ];
    const statuses = quotes.map((q) => q.freshness_status ?? "unknown");
    for (const level of priority) {
      if (statuses.includes(level)) return level;
    }
    return "unknown";
  }, [quotes]);

  return (
    <div className="p-8 space-y-6 max-w-[1400px]">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-heading-md text-on-dark">Mercados</h1>
          <p className="text-caption text-stone mt-1">
            Seguimiento en tiempo real de índices, divisas, cripto, bonos y materias primas.
          </p>
        </div>
        <div className="flex items-center gap-3 flex-shrink-0 pt-1">
          <LiveIndicator secondsSinceUpdate={secondsSinceUpdate} freshnessStatus={freshnessStatus} />
          <button
            type="button"
            onClick={refresh}
            disabled={refreshing}
            className="inline-flex items-center gap-2 rounded-md border border-hairline-dark bg-surface-elevated px-3 py-1.5 text-caption font-medium text-on-dark transition-colors hover:bg-surface-card disabled:cursor-not-allowed disabled:opacity-60"
          >
            <RefreshCw size={14} className={refreshing ? "animate-spin" : ""} />
            {refreshing ? "Actualizando..." : "Actualizar"}
          </button>
        </div>
      </div>

      {/* Category tabs */}
      <CategoryTabs activeCategory={activeCategory} onSelect={setActiveCategory} />

      {/* States */}
      {loading && <LoadingSkeleton />}
      {error && !loading && <ErrorState message={error} />}
      {isEmpty && <EmptyState noData={isInitial} />}

      {/* All categories grouped */}
      {hasData && activeCategory === "all" && (
        <div className="rounded-lg border border-hairline-dark bg-surface-elevated overflow-hidden">
          <TableHeader />
          {CATEGORY_ORDER.map((cat, catIdx) => {
            const catQuotes = visibleQuotes.filter((q) => q.category === cat.key);
            if (!catQuotes.length) return null;
            return (
              <div key={cat.key}>
                {catIdx > 0 && <div className="border-t border-hairline-dark" />}
                <div className="px-6 pt-4 pb-2">
                  <span className="text-caption text-mute uppercase tracking-widest font-medium">
                    {cat.label}
                  </span>
                </div>
                <div className="divide-y divide-divider-soft">
                  {catQuotes.map((q) => (
                    <QuoteRow
                      key={q.symbol}
                      quote={q}
                      isSelected={selectedSymbol === q.symbol}
                      onSelect={handleSelectAsset}
                    />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Single category flat list */}
      {hasData && activeCategory !== "all" && (
        <QuoteGroupPanel
          quotes={visibleQuotes}
          selectedSymbol={selectedSymbol}
          onSelect={handleSelectAsset}
        />
      )}
    </div>
  );
}
