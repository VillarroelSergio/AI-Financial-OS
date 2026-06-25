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
    <div className="flex flex-wrap gap-2">
      {TABS.map((tab) => (
        <button
          key={tab.value}
          onClick={() => onSelect(tab.value)}
          className={`text-button-sm rounded-full px-[14px] py-[6px] h-8 transition-colors duration-150 ${
            activeCategory === tab.value
              ? "bg-primary text-on-primary"
              : "bg-surface-elevated text-stone border border-hairline-dark hover:text-on-dark"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}
