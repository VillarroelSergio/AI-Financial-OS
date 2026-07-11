import { formatCurrency } from "@/lib/formatters/currency";
import type { HoldingEnriched } from "@/lib/types";
import PositionMenu, { type MenuItem } from "./PositionMenu";

interface HoldingRowProps {
  holding: HoldingEnriched;
  canMerge?: boolean;
  onEdit?: (holding: HoldingEnriched) => void;
  onDelete?: (holding: HoldingEnriched) => void;
  onMerge?: (holding: HoldingEnriched) => void;
  onHistory?: (holding: HoldingEnriched) => void;
  onFundValue?: (holding: HoldingEnriched) => void;
}

export default function HoldingRow({ holding, canMerge, onEdit, onDelete, onMerge, onHistory, onFundValue }: HoldingRowProps) {
  const isFund = holding.asset_type === "fund";
  const pct = holding.return_percent;
  const isPositive = pct !== null && pct >= 0;
  const updated = holding.current_price_updated_at
    ? new Date(holding.current_price_updated_at).toLocaleDateString("es-ES", {
        day: "2-digit",
        month: "2-digit",
      })
    : null;

  const items: MenuItem[] = [];
  if (onEdit) items.push({ label: "Editar", onClick: () => onEdit(holding) });
  if (isFund && onFundValue) items.push({ label: "Actualizar valor", onClick: () => onFundValue(holding) });
  else if (onHistory) items.push({ label: "Historial", onClick: () => onHistory(holding) });
  if (canMerge && onMerge) items.push({ label: "Fusionar duplicado", onClick: () => onMerge(holding) });
  if (onDelete) items.push({ label: "Eliminar", onClick: () => onDelete(holding), danger: true });

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
        {items.length > 0 && <PositionMenu items={items} />}
      </div>
    </div>
  );
}
