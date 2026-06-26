import { formatCurrency } from "@/lib/formatters/currency";
import type { HoldingEnriched } from "@/lib/types";

interface SavingsAccountCardProps {
  holding: HoldingEnriched;
}

export default function SavingsAccountCard({ holding }: SavingsAccountCardProps) {
  const tae = holding.interest_rate
    ? (parseFloat(holding.interest_rate) * 100).toFixed(2)
    : null;
  const displayValue = holding.market_value ?? holding.cost_basis;

  return (
    <div className="flex items-center justify-between py-sm">
      <div>
        <p className="text-body-sm text-on-dark">{holding.asset.name}</p>
        {tae && <p className="text-caption text-stone">TAE {tae}%</p>}
      </div>
      <div className="text-right">
        <p className="text-body-sm text-on-dark">{formatCurrency(displayValue)}</p>
        {holding.accrued_interest && (
          <p className="text-caption text-accent-teal">
            +{formatCurrency(holding.accrued_interest)} acumulado
          </p>
        )}
      </div>
    </div>
  );
}
