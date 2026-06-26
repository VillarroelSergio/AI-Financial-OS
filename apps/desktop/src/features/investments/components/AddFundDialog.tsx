import { useState } from "react";
import { createAsset, createHolding } from "@/lib/api/investments";

interface AddFundDialogProps {
  open: boolean;
  accountId: string;
  onClose: () => void;
  onSuccess: () => void;
}

export default function AddFundDialog({ open, accountId, onClose, onSuccess }: AddFundDialogProps) {
  const [name, setName] = useState("");
  const [isin, setIsin] = useState("");
  const [participaciones, setParticipaciones] = useState("");
  const [precioCompra, setPrecioCompra] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const reset = () => {
    setName("");
    setIsin("");
    setParticipaciones("");
    setPrecioCompra("");
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
        isin: isin || null,
        asset_type: "fund",
        currency: "EUR",
        price_source: "manual",
      });
      await createHolding({
        account_id: accountId,
        asset_id: asset.id,
        quantity: participaciones,
        average_price: precioCompra,
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
        <h2 className="text-heading-sm text-on-dark mb-xl">Añadir fondo</h2>
        <form onSubmit={handleSubmit} className="space-y-md">
          <div>
            <label className="text-caption text-stone block mb-xs">Nombre del fondo</label>
            <input
              className="w-full bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="Vanguard US 500 Index Inst Plus"
              required
            />
          </div>
          <div>
            <label className="text-caption text-stone block mb-xs">ISIN (opcional)</label>
            <input
              className="w-full bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
              value={isin}
              onChange={e => setIsin(e.target.value)}
              placeholder="IE00B5B3X895"
            />
          </div>
          <div className="grid grid-cols-2 gap-md">
            <div>
              <label className="text-caption text-stone block mb-xs">Participaciones</label>
              <input
                type="number"
                step="0.000001"
                min="0"
                className="w-full bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={participaciones}
                onChange={e => setParticipaciones(e.target.value)}
                placeholder="4.59"
                required
              />
            </div>
            <div>
              <label className="text-caption text-stone block mb-xs">Precio compra (EUR)</label>
              <input
                type="number"
                step="0.01"
                min="0"
                className="w-full bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={precioCompra}
                onChange={e => setPrecioCompra(e.target.value)}
                placeholder="420.00"
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
