type RegionTab = "ES" | "EA" | "US";

const TABS: Array<{ value: RegionTab; label: string }> = [
  { value: "ES", label: "España" },
  { value: "EA", label: "Eurozona" },
  { value: "US", label: "EEUU" },
];

interface Props {
  active: RegionTab;
  onSelect: (r: RegionTab) => void;
}

export default function RegionTabs({ active, onSelect }: Props) {
  return (
    <div
      role="tablist"
      aria-label="Seleccionar región"
      className="flex gap-1.5"
    >
      {TABS.map((tab) => {
        const isActive = active === tab.value;
        return (
          <button
            key={tab.value}
            role="tab"
            aria-selected={isActive}
            onClick={() => onSelect(tab.value)}
            className={[
              "flex-shrink-0 text-button-sm rounded-full px-3.5 py-1.5 h-8 transition-all duration-150",
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

export type { RegionTab };
