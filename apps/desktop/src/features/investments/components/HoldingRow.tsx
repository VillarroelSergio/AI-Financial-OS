import { formatCurrency } from "@/lib/formatters/currency";
import type { HoldingEnriched } from "@/lib/types";

interface HoldingRowProps {
  holding: HoldingEnriched;
  onEdit?: (holding: HoldingEnriched) => void;
  onDelete?: (holding: HoldingEnriched) => void;
}

export default function HoldingRow({ holding, onEdit, onDelete }: HoldingRowProps) {
  const pct = holding.return_percent;
  const isPositive = pct !== null && pct >= 0;
  const updated = holding.current_price_updated_at
    ? new Date(holding.current_price_updated_at).toLocaleDateString("es-ES", {
        day: "2-digit",
        month: "2-digit",
      })
    : null;

  return (
    <div className="flex items-center justify-between py-sm gap-md">
      <div className="min-w-0">
        <div className="flex items-center gap-sm">
          <p className="text-body-sm text-on-dark truncate">{holding.display_name}</p>
          {holding.is_mock && <span className="rounded-full bg-amber-400/15 px-2 py-0.5 text-[10px] text-amber-300">Demo</span>}
        </div>
        <p className="text-caption text-stone">
          {[holding.symbol, holding.asset_type, holding.currency].filter(Boolean).join(" · ")}
        </p>
        {holding.warnings.length > 0 && <p className="text-[11px] text-amber-300 truncate">{holding.warnings[0]}</p>}
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
            className={`text-xs font-medium px-2 py-0.5 rounded-full ${
              isPositive
                ? "bg-accent-teal/10 text-accent-teal"
                : "bg-accent-danger/10 text-accent-danger"
            }`}
          >
            {isPositive ? "+" : ""}
            {pct.toFixed(1)}%
          </span>
        )}
        <div className="flex flex-col gap-xs">
          {onEdit && <button onClick={() => onEdit(holding)} className="text-caption text-stone hover:text-on-dark">Editar</button>}
          {onDelete && <button onClick={() => onDelete(holding)} className="text-caption text-stone hover:text-accent-danger">Eliminar</button>}
        </div>
      </div>
    </div>
  );
}
