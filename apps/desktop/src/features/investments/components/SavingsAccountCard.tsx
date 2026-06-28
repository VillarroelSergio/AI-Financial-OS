import { formatCurrency } from "@/lib/formatters/currency";
import type { HoldingEnriched } from "@/lib/types";

interface SavingsAccountCardProps {
  holding: HoldingEnriched;
  onEdit?: (holding: HoldingEnriched) => void;
  onDelete?: (holding: HoldingEnriched) => void;
}

export default function SavingsAccountCard({ holding, onEdit, onDelete }: SavingsAccountCardProps) {
  const tae = holding.interest_rate
    ? (parseFloat(holding.interest_rate) * 100).toFixed(2)
    : null;
  const displayValue = holding.market_value ?? holding.cost_basis;

  return (
    <div className="flex items-center justify-between py-sm">
      <div>
        <p className="text-body-sm text-on-dark">{holding.display_name}</p>
        {tae && <p className="text-caption text-stone">TAE {tae}%</p>}
      </div>
      <div className="flex items-center gap-md">
        <div className="text-right">
        <p className="text-body-sm text-on-dark">{formatCurrency(displayValue)}</p>
        {holding.accrued_interest && (
          <p className="text-caption text-accent-teal">
            +{formatCurrency(holding.accrued_interest)} acumulado
          </p>
        )}
        </div>
        <div className="flex flex-col gap-xs">
          {onEdit && <button onClick={() => onEdit(holding)} className="text-caption text-stone hover:text-on-dark">Editar</button>}
          {onDelete && <button onClick={() => onDelete(holding)} className="text-caption text-stone hover:text-accent-danger">Eliminar</button>}
        </div>
      </div>
    </div>
  );
}
