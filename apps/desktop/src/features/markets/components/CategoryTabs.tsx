// apps/desktop/src/features/markets/components/CategoryTabs.tsx
import type { MarketCategory } from "@/lib/types";

const TABS: Array<{ value: MarketCategory | "all"; label: string }> = [
  { value: "all", label: "Todos" },
  { value: "indices_eu", label: "Europa" },
  { value: "indices_us", label: "EEUU" },
  { value: "indices_asia", label: "Asia" },
  { value: "crypto", label: "Cripto" },
  { value: "fx", label: "Divisas" },
  { value: "bonds", label: "Bonos" },
  { value: "commodities", label: "Mat. Primas" },
  { value: "volatility", label: "Volatilidad" },
];

interface Props {
  activeCategory: MarketCategory | "all";
  onSelect: (cat: MarketCategory | "all") => void;
}

export default function CategoryTabs({ activeCategory, onSelect }: Props) {
  return (
    <div
      role="tablist"
      aria-label="Filtrar por categoría de mercado"
      className="flex gap-1.5 overflow-x-auto pb-0.5 scrollbar-none"
      style={{ scrollbarWidth: "none" }}
    >
      {TABS.map((tab) => {
        const isActive = activeCategory === tab.value;
        return (
          <button
            key={tab.value}
            role="tab"
            aria-selected={isActive}
            onClick={() => onSelect(tab.value)}
            className={[
              "ui-pressable flex-shrink-0 text-button-sm rounded-full px-3.5 py-1.5 h-8",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 focus-visible:ring-offset-canvas-dark",
              isActive
                ? "bg-primary text-on-dark shadow-[0_0_0_1px_rgba(73,79,223,0.6)] font-medium"
                : "bg-surface-elevated text-stone border border-hairline-dark hover:text-on-dark hover:border-primary/40 hover:bg-surface-card",
            ].join(" ")}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
