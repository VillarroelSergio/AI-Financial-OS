import { useState } from "react";
import { createAsset, createHolding } from "@/lib/api/investments";

interface AddSavingsDialogProps {
  open: boolean;
  accountId: string;
  onClose: () => void;
  onSuccess: () => void;
}

export default function AddSavingsDialog({ open, accountId, onClose, onSuccess }: AddSavingsDialogProps) {
  const [name, setName] = useState("");
  const [saldo, setSaldo] = useState("");
  const [tae, setTae] = useState("");
  const [fechaInicio, setFechaInicio] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const reset = () => {
    setName("");
    setSaldo("");
    setTae("");
    setFechaInicio("");
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
        asset_type: "savings_account",
        currency: "EUR",
        price_source: "manual",
      });
      const taeDecimal = (parseFloat(tae) / 100).toFixed(4);
      await createHolding({
        account_id: accountId,
        asset_id: asset.id,
        quantity: saldo,
        average_price: "1",
        market_value: saldo,
        interest_rate: taeDecimal,
        inception_date: fechaInicio || undefined,
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
        <h2 className="text-heading-sm text-on-dark mb-xl">Añadir cuenta de ahorro</h2>
        <form onSubmit={handleSubmit} className="space-y-md">
          <div>
            <label className="text-caption text-stone block mb-xs">Nombre</label>
            <input
              className="w-full bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Cuenta Remunerada Trade Republic"
              required
            />
          </div>
          <div className="grid grid-cols-2 gap-md">
            <div>
              <label className="text-caption text-stone block mb-xs">Saldo (EUR)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                className="w-full bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={saldo}
                onChange={e => setSaldo(e.target.value)}
                placeholder="5000.00"
                required
              />
            </div>
            <div>
              <label className="text-caption text-stone block mb-xs">TAE (%)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                className="w-full bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={tae}
                onChange={e => setTae(e.target.value)}
                placeholder="4.00"
                required
              />
            </div>
          </div>
          <div>
            <label className="text-caption text-stone block mb-xs">Fecha de inicio</label>
            <input
              type="date"
              className="w-full bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
              value={fechaInicio}
              onChange={e => setFechaInicio(e.target.value)}
            />
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
