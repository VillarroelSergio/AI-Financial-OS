import { useState } from "react";
import { createSavings } from "@/lib/api/investments";
import { formatCurrency } from "@/lib/formatters/currency";

interface AddSavingsDialogProps {
  open: boolean;
  accountId: string;
  onClose: () => void;
  onSuccess: () => void;
}

// Preview compuesto mensual (espeja el motor determinista para modo fijo).
function estimateInterest(balance: number, annualPct: number, openedAt: string): number | null {
  if (!Number.isFinite(balance) || !Number.isFinite(annualPct) || !openedAt) return null;
  const start = new Date(`${openedAt}T00:00:00`);
  const now = new Date();
  let months = (now.getFullYear() - start.getFullYear()) * 12 + (now.getMonth() - start.getMonth()) + 1;
  if (months <= 0) return 0;
  const factor = annualPct / 100 / 12;
  let bal = balance;
  for (let i = 0; i < months; i++) bal += bal * factor;
  return bal - balance;
}

export default function AddSavingsDialog({ open, accountId, onClose, onSuccess }: AddSavingsDialogProps) {
  const [name, setName] = useState("Cuenta Remunerada Trade Republic");
  const [saldo, setSaldo] = useState("");
  const [rateSource, setRateSource] = useState<"ecb_deposit_facility" | "fixed">("ecb_deposit_facility");
  const [tae, setTae] = useState("");
  const [fechaInicio, setFechaInicio] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const reset = () => {
    setName("Cuenta Remunerada Trade Republic");
    setSaldo("");
    setRateSource("ecb_deposit_facility");
    setTae("");
    setFechaInicio("");
    setError(null);
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const preview =
    rateSource === "fixed" ? estimateInterest(parseFloat(saldo), parseFloat(tae), fechaInicio) : null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await createSavings({
        account_id: accountId || undefined,
        new_account_name: accountId ? undefined : name,
        opened_at: fechaInicio,
        balance: saldo,
        rate_source: rateSource,
        fixed_rate: rateSource === "fixed" ? tae : undefined,
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
                type="number" step="0.01" min="0"
                className="w-full bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={saldo}
                onChange={e => setSaldo(e.target.value)}
                placeholder="5000.00"
                required
              />
            </div>
            <div>
              <label className="text-caption text-stone block mb-xs">Fecha de apertura</label>
              <input
                type="date" required
                className="w-full bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
                value={fechaInicio}
                onChange={e => setFechaInicio(e.target.value)}
              />
            </div>
          </div>
          <div>
            <label className="text-caption text-stone block mb-xs">Tipo de interés</label>
            <select
              className="w-full bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
              value={rateSource}
              onChange={e => setRateSource(e.target.value as "ecb_deposit_facility" | "fixed")}
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
                onChange={e => setTae(e.target.value)}
                placeholder="4.00"
                required
              />
            </div>
          )}
          {preview !== null && (
            <p className="text-caption text-stone">
              Intereses estimados desde apertura:{" "}
              <span className="text-accent-teal">+{formatCurrency(preview.toFixed(2))}</span>
            </p>
          )}
          {rateSource === "ecb_deposit_facility" && (
            <p className="text-caption text-mute">La serie exacta con el tipo BCE se calcula al guardar (ver "Evolución").</p>
          )}
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
