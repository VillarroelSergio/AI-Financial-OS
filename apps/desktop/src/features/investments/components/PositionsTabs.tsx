import { useState } from "react";
import type { HoldingEnriched } from "@/lib/types";
import HoldingRow from "./HoldingRow";
import SavingsAccountCard from "./SavingsAccountCard";

type TabKey = "tr" | "finizens" | "ahorro";

const TABS: { key: TabKey; label: string }[] = [
  { key: "tr", label: "Trade Republic" },
  { key: "finizens", label: "Finizens" },
  { key: "ahorro", label: "Ahorro" },
];

interface PositionsTabsProps {
  holdings: HoldingEnriched[];
  trAccountIds: string[];
  finizensAccountIds: string[];
  ahorroAccountIds: string[];
  onAddStock: () => void;
  onAddFund: () => void;
  onAddSavings: () => void;
}

export default function PositionsTabs({
  holdings,
  trAccountIds,
  finizensAccountIds,
  ahorroAccountIds,
  onAddStock,
  onAddFund,
  onAddSavings,
}: PositionsTabsProps) {
  const [active, setActive] = useState<TabKey>("tr");

  const filteredHoldings = holdings.filter((h) => {
    if (active === "tr")
      return trAccountIds.includes(h.account_id) && h.asset.asset_type !== "savings_account";
    if (active === "finizens") return finizensAccountIds.includes(h.account_id);
    return ahorroAccountIds.includes(h.account_id);
  });

  const addLabel =
    active === "tr"
      ? "+ Añadir acción"
      : active === "finizens"
        ? "+ Añadir fondo"
        : "+ Añadir cuenta de ahorro";

  const addAction =
    active === "tr" ? onAddStock : active === "finizens" ? onAddFund : onAddSavings;

  return (
    <div className="bg-surface-card border border-hairline-dark rounded-md p-xl flex flex-col">
      <div className="flex gap-sm mb-lg flex-wrap">
        {TABS.map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setActive(key)}
            className={`px-md py-xs rounded-full text-caption transition-colors ${
              active === key
                ? "bg-primary text-on-primary"
                : "bg-surface-elevated text-stone-400 hover:text-on-dark"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="flex-1 divide-y divide-hairline-dark">
        {filteredHoldings.length === 0 ? (
          <p className="text-caption text-stone py-md text-center">
            Sin posiciones en este broker
          </p>
        ) : (
          filteredHoldings.map((h) =>
            h.asset.asset_type === "savings_account" ? (
              <SavingsAccountCard key={h.id} holding={h} />
            ) : (
              <HoldingRow key={h.id} holding={h} />
            ),
          )
        )}
      </div>

      <button
        onClick={addAction}
        className="mt-lg text-caption text-stone hover:text-on-dark transition-colors text-left"
      >
        {addLabel}
      </button>
    </div>
  );
}
