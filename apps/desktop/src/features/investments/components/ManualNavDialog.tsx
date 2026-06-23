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
  const [navValues, setNavValues] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open || holdings.length === 0) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await Promise.all(
        holdings.map(h => {
          const nav = navValues[h.id];
          return nav ? updateHolding(h.id, { current_price: nav }) : Promise.resolve(h);
        })
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
      <div className="bg-surface-elevated border border-hairline-dark rounded-xl p-2xl w-full max-w-md">
        <h2 className="text-heading-sm text-on-dark mb-xs">Actualizar NAV</h2>
        <p className="text-body-sm text-stone mb-xl">
          Introduce el valor liquidativo actual de cada fondo. Consúltalo en el portal de tu gestora.
        </p>
        <form onSubmit={handleSubmit} className="space-y-md">
          {holdings.map(h => (
            <div key={h.id}>
              <label className="text-caption text-stone block mb-xs">{h.asset.name}</label>
              <input
                type="number"
                step="0.01"
                min="0"
                className="w-full bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={navValues[h.id] ?? ""}
                onChange={e => setNavValues(prev => ({ ...prev, [h.id]: e.target.value }))}
                placeholder={h.current_price ?? "0.00"}
              />
            </div>
          ))}
          {error && <p className="text-caption text-accent-danger">{error}</p>}
          <div className="flex gap-md justify-end pt-sm">
            <button
              type="button"
              onClick={onClose}
              className="px-lg py-sm rounded-md text-body-sm text-stone hover:text-on-dark transition-colors"
            >
              Ahora no
            </button>
            <button
              type="submit"
              disabled={saving}
              className="px-lg py-sm rounded-md text-body-sm bg-primary text-on-primary hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {saving ? "Guardando..." : "Guardar NAV"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
