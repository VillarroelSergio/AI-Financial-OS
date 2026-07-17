import { useState } from "react";
import { updateHolding } from "@/lib/api/investments";
import { formatCurrency } from "@/lib/formatters/currency";
import type { HoldingEnriched } from "@/lib/types";

interface ManualNavDialogProps {
  open: boolean;
  holdings: HoldingEnriched[];
  onClose: () => void;
  onSuccess: () => void;
}

export default function ManualNavDialog({ open, holdings, onClose, onSuccess }: ManualNavDialogProps) {
  const investableHoldings = holdings.filter((h) => !["cash", "savings_account"].includes(h.asset_type));
  const [priceValues, setPriceValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open || investableHoldings.length === 0) return null;

  const handleClose = () => {
    setPriceValues({});
    setError(null);
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await Promise.all(
        investableHoldings.map((holding) => {
          const price = priceValues[holding.id];
          return price ? updateHolding(holding.id, { current_price: price }) : Promise.resolve(holding);
        }),
      );
      onSuccess();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    } finally {
      setSaving(false);
    }
  };

  const getGuidance = (holding: HoldingEnriched) => {
    const isFund = holding.asset_type === "fund";
    const units = Number(holding.quantity);
    const enteredValue = priceValues[holding.id];
    const enteredPrice = Number(enteredValue);
    const estimatedValue = enteredValue !== undefined && enteredValue !== "" && Number.isFinite(enteredPrice) && enteredPrice >= 0
      ? enteredPrice * (Number.isFinite(units) ? units : 0)
      : null;

    return {
      label: isFund ? "Valor liquidativo por participación" : "Cotización por unidad",
      help: isFund
        ? `Introduce el NAV de una participación que muestra tu gestora, no el valor total de la inversión. Tienes ${holding.quantity} participaciones.`
        : "Introduce el precio de una unidad del activo, no el valor total de tu posición.",
      estimatedValue,
    };
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 p-4">
      <div className="flex max-h-[calc(100vh-2rem)] w-full max-w-2xl flex-col rounded-xl border border-hairline-dark bg-surface-elevated p-2xl">
        <h2 className="mb-xs text-heading-sm text-on-dark">Completar precios faltantes</h2>
        <p className="mb-md text-body-sm text-stone">
          Algunos activos no tienen proveedor de precios automático. Introduce el precio por unidad que muestra tu bróker o gestora para actualizar su valoración.
        </p>
        <p className="mb-xl text-body-sm text-mute">
          En fondos, el valor solicitado es el <strong>valor liquidativo (NAV) de una participación</strong>, no el importe total invertido. Puedes dejar vacío cualquier activo que no quieras actualizar ahora.
        </p>
        <form onSubmit={handleSubmit} className="flex min-h-0 flex-1 flex-col">
          <div className="space-y-lg overflow-y-auto pr-1">
          {investableHoldings.map((holding) => (
            <div key={holding.id} className="rounded-lg border border-hairline-dark bg-[var(--bg-interactive)] p-4">
              <p className="mb-1 text-body-sm font-semibold text-on-dark">
                {holding.display_name} · {holding.asset_type} · {holding.currency}
              </p>
              {(() => {
                const guidance = getGuidance(holding);
                return <>
                  <label className="mb-xs block text-body-sm text-stone" htmlFor={`manual-price-${holding.id}`}>
                    {guidance.label} ({holding.currency})
                  </label>
                  <p className="mb-sm text-caption text-mute">{guidance.help}</p>
              <input
                id={`manual-price-${holding.id}`}
                type="number"
                step="0.0001"
                min="0"
                className="w-full rounded-md border border-hairline-dark bg-canvas-dark px-md py-sm text-body-sm text-on-dark focus:border-primary focus:outline-none"
                value={priceValues[holding.id] ?? ""}
                onChange={(e) => setPriceValues((prev) => ({ ...prev, [holding.id]: e.target.value }))}
                placeholder={holding.current_price ?? "0.00"}
              />
                  <p className="mt-2 text-caption text-stone">
                    {guidance.estimatedValue !== null
                      ? `Valor estimado de la posición: ${formatCurrency(guidance.estimatedValue, holding.currency)}`
                      : `Precio actual guardado: ${holding.current_price ? formatCurrency(Number(holding.current_price), holding.currency) : "sin dato"}`}
                  </p>
                </>;
              })()}
            </div>
          ))}
          </div>
          {error && <p className="text-caption text-accent-danger">{error}</p>}
          <div className="flex justify-end gap-md pt-lg">
            <button
              type="button"
              onClick={handleClose}
              className="rounded-md px-lg py-sm text-body-sm text-stone transition-colors hover:text-on-dark"
            >
              Ahora no
            </button>
            <button
              type="submit"
              disabled={saving}
              className="rounded-md bg-primary px-lg py-sm text-body-sm text-on-primary transition-colors hover:bg-primary/90 disabled:opacity-50"
            >
              {saving ? "Guardando..." : "Guardar precios"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
