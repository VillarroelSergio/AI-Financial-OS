import { useEffect, useState } from "react";
import { getSavingsConfig, updateSavings } from "@/lib/api/investments";
import type { HoldingEnriched } from "@/lib/types";

interface SavingsEditDialogProps {
  holding: HoldingEnriched | null;
  onClose: () => void;
  onSaved: () => void;
}

/** Edición de la configuración de una cuenta remunerada (tipo/TAE/fecha). INV-5. */
export default function SavingsEditDialog({ holding, onClose, onSaved }: SavingsEditDialogProps) {
  const [rateSource, setRateSource] = useState<"ecb_deposit_facility" | "fixed">("ecb_deposit_facility");
  const [tae, setTae] = useState("");
  const [openedAt, setOpenedAt] = useState("");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!holding) return;
    setError(null);
    setLoading(true);
    getSavingsConfig(holding.account_id)
      .then((cfg) => {
        setRateSource(cfg.rate_source === "fixed" ? "fixed" : "ecb_deposit_facility");
        setTae(cfg.fixed_rate ?? "");
        setOpenedAt(cfg.opened_at ?? "");
      })
      .catch((e) => setError(e instanceof Error ? e.message : "No se pudo cargar la configuración"))
      .finally(() => setLoading(false));
  }, [holding]);

  if (!holding) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await updateSavings(holding.account_id, {
        rate_source: rateSource,
        fixed_rate: rateSource === "fixed" ? tae : null,
        opened_at: openedAt || undefined,
      });
      onSaved();
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
        <h2 className="text-heading-sm text-on-dark mb-xl">Editar cuenta de ahorro</h2>
        {loading ? (
          <p className="text-caption text-stone">Cargando…</p>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-md">
            <div>
              <label className="text-caption text-stone block mb-xs">Fecha de apertura</label>
              <input
                type="date"
                className="w-full bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={openedAt}
                onChange={(e) => setOpenedAt(e.target.value)}
              />
            </div>
            <div>
              <label className="text-caption text-stone block mb-xs">Tipo de interés</label>
              <select
                className="w-full bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={rateSource}
                onChange={(e) => setRateSource(e.target.value as "ecb_deposit_facility" | "fixed")}
              >
                <option value="ecb_deposit_facility">BCE — facilidad de depósito</option>
                <option value="fixed">Fijo</option>
              </select>
            </div>
            {rateSource === "fixed" && (
              <div>
                <label className="text-caption text-stone block mb-xs">TAE (%)</label>
                <input
                  type="number" step="0.01" min="0"
                  className="w-full bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                  value={tae}
                  onChange={(e) => setTae(e.target.value)}
                  placeholder="4.00"
                  required
                />
              </div>
            )}
            {error && <p className="text-caption text-accent-danger">{error}</p>}
            <div className="flex gap-md justify-end pt-sm">
              <button
                type="button"
                onClick={onClose}
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
        )}
      </div>
    </div>
  );
}
