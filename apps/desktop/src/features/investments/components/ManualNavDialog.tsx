import { useState } from "react";
import { updateHolding } from "@/lib/api/investments";
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

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-lg rounded-xl border border-hairline-dark bg-surface-elevated p-2xl">
        <h2 className="mb-xs text-heading-sm text-on-dark">Completar precios faltantes</h2>
        <p className="mb-md text-body-sm text-stone">
          Algunos activos no tienen proveedor de precios automatico. Introduce un precio manual si quieres actualizar su valoracion.
        </p>
        <p className="mb-xl text-caption text-mute">
          Precio actual: valor usado para calcular la posicion. NAV solo aplica a fondos; no se pide para cuentas remuneradas o efectivo.
        </p>
        <form onSubmit={handleSubmit} className="space-y-md">
          {investableHoldings.map((holding) => (
            <div key={holding.id}>
              <label className="mb-xs block text-caption text-stone">
                {holding.display_name} · {holding.asset_type} · {holding.currency}
              </label>
              <input
                type="number"
                step="0.01"
                min="0"
                className="w-full rounded-md border border-hairline-dark bg-canvas-dark px-md py-sm text-body-sm text-on-dark focus:border-primary focus:outline-none"
                value={priceValues[holding.id] ?? ""}
                onChange={(e) => setPriceValues((prev) => ({ ...prev, [holding.id]: e.target.value }))}
                placeholder={holding.current_price ?? "0.00"}
              />
            </div>
          ))}
          {error && <p className="text-caption text-accent-danger">{error}</p>}
          <div className="flex justify-end gap-md pt-sm">
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
