import { useState } from "react";
import { createAsset, createHolding } from "@/lib/api/investments";

interface AddStockDialogProps {
  open: boolean;
  accountId: string;
  onClose: () => void;
  onSuccess: () => void;
}

export default function AddStockDialog({ open, accountId, onClose, onSuccess }: AddStockDialogProps) {
  const [ticker, setTicker] = useState("");
  const [name, setName] = useState("");
  const [currency, setCurrency] = useState("EUR");
  const [quantity, setQuantity] = useState("");
  const [avgPrice, setAvgPrice] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const reset = () => {
    setTicker("");
    setName("");
    setQuantity("");
    setAvgPrice("");
    setError(null);
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const asset = await createAsset({
        name,
        ticker,
        asset_type: "stock",
        currency,
        price_source: "yfinance",
      });
      await createHolding({
        account_id: accountId,
        asset_id: asset.id,
        quantity,
        average_price: avgPrice,
      });
      reset();
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
      <div className="bg-surface-elevated border border-hairline-dark rounded-xl p-2xl w-full max-w-md">
        <h2 className="text-heading-sm text-on-dark mb-xl">Añadir acción</h2>
        <form onSubmit={handleSubmit} className="space-y-md">
          <div className="grid grid-cols-2 gap-md">
            <div>
              <label className="text-caption text-stone block mb-xs">Ticker</label>
              <input
                className="w-full bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={ticker}
                onChange={e => setTicker(e.target.value)}
                placeholder="TEF.MC"
                required
              />
            </div>
            <div>
              <label className="text-caption text-stone block mb-xs">Divisa</label>
              <select
                className="w-full bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={currency}
                onChange={e => setCurrency(e.target.value)}
              >
                <option value="EUR">EUR</option>
                <option value="USD">USD</option>
                <option value="GBP">GBP</option>
              </select>
            </div>
          </div>
          <div>
            <label className="text-caption text-stone block mb-xs">Nombre</label>
            <input
              className="w-full bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Telefónica"
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-md">
            <div>
              <label className="text-caption text-stone block mb-xs">Acciones</label>
              <input
                type="number"
                step="0.000001"
                min="0.000001"
                className="w-full bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={quantity}
                onChange={e => setQuantity(e.target.value)}
                placeholder="100"
                required
              />
            </div>
            <div>
              <label className="text-caption text-stone block mb-xs">Precio compra</label>
              <input
                type="number"
                step="0.01"
                min="0.01"
                className="w-full bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={avgPrice}
                onChange={e => setAvgPrice(e.target.value)}
                placeholder="3.95"
                required
              />
            </div>
          </div>
          {error && <p className="text-caption text-accent-danger">{error}</p>}
          <div className="flex gap-md justify-end pt-sm">
            <button
              type="button"
              onClick={handleClose}
              className="px-lg py-sm rounded-md text-body-sm text-stone hover:text-on-dark transition-colors"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-lg py-sm rounded-md text-body-sm bg-primary text-on-primary hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {saving ? "Guardando..." : "Guardar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
