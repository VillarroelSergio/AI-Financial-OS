import { formatCurrency } from "@/lib/formatters/currency";
import type { HoldingEnriched } from "@/lib/types";

interface HoldingRowProps {
  holding: HoldingEnriched;
}

export default function HoldingRow({ holding }: HoldingRowProps) {
  const pct = holding.return_percent;
  const isPositive = pct !== null && pct >= 0;
  const updated = holding.current_price_updated_at
    ? new Date(holding.current_price_updated_at).toLocaleDateString("es-ES", {
        day: "2-digit",
        month: "2-digit",
      })
    : null;

  return (
    <div className="flex items-center justify-between py-sm">
      <div className="min-w-0">
        <p className="text-body-sm text-on-dark truncate">{holding.asset.name}</p>
        {holding.asset.ticker && (
          <p className="text-caption text-stone">{holding.asset.ticker}</p>
        )}
      </div>
      <div className="flex items-center gap-md flex-shrink-0 ml-md">
        <div className="text-right">
          <p className="text-body-sm text-on-dark">
            {holding.market_value ? formatCurrency(holding.market_value) : "—"}
          </p>
          {updated && <p className="text-caption text-stone">{updated}</p>}
        </div>
        {pct !== null && (
          <span
            className={`text-caption font-medium px-sm py-xs rounded-full min-w-[52px] text-center ${
              isPositive
                ? "bg-accent-teal/10 text-accent-teal"
                : "bg-accent-danger/10 text-accent-danger"
            }`}
          >
            {isPositive ? "+" : ""}
            {pct.toFixed(1)}%
          </span>
        )}
      </div>
    </div>
  );
}
