import { useState } from "react";
import { createFund } from "@/lib/api/investments";
import { formatCurrency } from "@/lib/formatters/currency";
import type { Account } from "@/lib/types";

interface AddFundDialogProps {
  open: boolean;
  accountId: string;
  accounts: Account[];
  onClose: () => void;
  onSuccess: () => void;
}

type Mode = "return" | "units";

const today = () => new Date().toISOString().slice(0, 10);

export default function AddFundDialog({ open, accountId, accounts, onClose, onSuccess }: AddFundDialogProps) {
  const [mode, setMode] = useState<Mode>("return");
  // El fondo debe colgar de una cuenta real; el default fijado por tipo puede no existir.
  const [account, setAccount] = useState(accountId || accounts[0]?.id || "");
  const [name, setName] = useState("");
  const [returnPct, setReturnPct] = useState("");
  const [value, setValue] = useState("");     // valor actual (vía rendimiento)
  const [units, setUnits] = useState("");     // nº participaciones (vía participaciones)
  const [nav, setNav] = useState("");         // valor liquidativo (vía participaciones)
  const [date, setDate] = useState(today());
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const reset = () => {
    setMode("return"); setAccount(accountId || accounts[0]?.id || "");
    setName(""); setReturnPct(""); setValue("");
    setUnits(""); setNav(""); setDate(today()); setError(null);
  };
  const handleClose = () => { reset(); onClose(); };

  // Valor actual: directo (rendimiento) o nº × valor liquidativo (participaciones).
  const u = parseFloat(units), n = parseFloat(nav);
  const currentValue = mode === "return"
    ? parseFloat(value)
    : (Number.isFinite(u) && Number.isFinite(n) ? u * n : NaN);

  // Aportado derivado del % rendimiento: aportado = valor / (1 + %/100).
  const pct = parseFloat(returnPct);
  const factor = 1 + (Number.isFinite(pct) ? pct : 0) / 100;
  const contributed = factor > 0 && Number.isFinite(currentValue) ? currentValue / factor : NaN;
  const gain = Number.isFinite(currentValue) && Number.isFinite(contributed) ? currentValue - contributed : null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!Number.isFinite(currentValue) || currentValue <= 0) {
      setError(mode === "return" ? "Introduce un valor actual válido" : "Introduce nº de participaciones y valor liquidativo");
      return;
    }
    if (factor <= 0) { setError("El % de rendimiento no puede ser ≤ −100%"); return; }
    if (!account) { setError("Selecciona una cuenta"); return; }
    setSaving(true);
    setError(null);
    try {
      await createFund({
        name, account_id: account,
        contributed: contributed.toFixed(2), value: currentValue.toFixed(2), date,
        units: mode === "units" ? u.toString() : null,
        nav: mode === "units" ? n.toString() : null,
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

  const inputCls = "w-full bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary";
  const tab = (m: Mode, label: string) => (
    <button
      type="button"
      onClick={() => setMode(m)}
      className={`flex-1 px-md py-sm rounded-md text-caption transition-colors ${
        mode === m ? "bg-primary text-on-primary" : "bg-canvas-dark text-stone hover:text-on-dark"
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="bg-surface-elevated border border-hairline-dark rounded-xl p-2xl w-full max-w-md">
        <h2 className="text-heading-sm text-on-dark mb-lg">Añadir fondo</h2>

        <div className="flex gap-sm mb-lg">
          {tab("return", "Por rendimiento")}
          {tab("units", "Por participaciones")}
        </div>

        <form onSubmit={handleSubmit} className="space-y-md">
          <div>
            <label className="text-caption text-stone block mb-xs">Cuenta</label>
            <select className={inputCls} value={account} onChange={e => setAccount(e.target.value)} required>
              {accounts.length === 0 && <option value="">Sin cuentas</option>}
              {accounts.map(a => <option key={a.id} value={a.id}>{a.name}</option>)}
            </select>
          </div>
          <div>
            <label className="text-caption text-stone block mb-xs">Nombre del fondo</label>
            <input className={inputCls} value={name} onChange={e => setName(e.target.value)}
              placeholder="Vanguard US 500 Index Inst Plus" required />
          </div>

          {mode === "return" ? (
            <div>
              <label className="text-caption text-stone block mb-xs">Valor actual (EUR)</label>
              <input type="number" step="0.01" min="0" className={inputCls} value={value}
                onChange={e => setValue(e.target.value)} placeholder="10850.00" required />
            </div>
          ) : (
            <div className="grid grid-cols-2 gap-md">
              <div>
                <label className="text-caption text-stone block mb-xs">Nº participaciones</label>
                <input type="number" step="0.000001" min="0" className={inputCls} value={units}
                  onChange={e => setUnits(e.target.value)} placeholder="4.59" required />
              </div>
              <div>
                <label className="text-caption text-stone block mb-xs">Valor liquidativo (EUR)</label>
                <input type="number" step="0.0001" min="0" className={inputCls} value={nav}
                  onChange={e => setNav(e.target.value)} placeholder="576.31" required />
              </div>
            </div>
          )}

          <div className="grid grid-cols-2 gap-md">
            <div>
              <label className="text-caption text-stone block mb-xs">Rendimiento (%)</label>
              <input type="number" step="0.01" className={inputCls} value={returnPct}
                onChange={e => setReturnPct(e.target.value)} placeholder="8.50" />
            </div>
            <div>
              <label className="text-caption text-stone block mb-xs">Fecha de valoración</label>
              <input type="date" required className={inputCls} value={date}
                onChange={e => setDate(e.target.value)} />
            </div>
          </div>

          {Number.isFinite(currentValue) && (
            <div className="rounded-md bg-canvas-dark border border-hairline-dark px-md py-sm space-y-xs">
              <div className="flex justify-between text-caption">
                <span className="text-stone">Valor actual</span>
                <span className="text-on-dark">{formatCurrency(currentValue.toFixed(2))}</span>
              </div>
              <div className="flex justify-between text-caption">
                <span className="text-stone">Aportado (derivado)</span>
                <span className="text-on-dark">{Number.isFinite(contributed) ? formatCurrency(contributed.toFixed(2)) : "—"}</span>
              </div>
              {gain !== null && (
                <div className="flex justify-between text-caption">
                  <span className="text-stone">Ganancia</span>
                  <span className={gain >= 0 ? "text-accent-teal" : "text-accent-danger"}>
                    {gain >= 0 ? "+" : ""}{formatCurrency(gain.toFixed(2))}
                  </span>
                </div>
              )}
            </div>
          )}

          <p className="text-caption text-mute">
            Sin cotización automática: actualiza el valor cuando quieras con "Actualizar valor"; se guarda un histórico editable.
            {mode === "units" && " El nº de participaciones ayuda a ver el peso del fondo."}
          </p>
          {error && <p className="text-caption text-accent-danger">{error}</p>}

          <div className="flex gap-md justify-end pt-sm">
            <button type="button" onClick={handleClose}
              className="px-lg py-sm rounded-md text-body-sm text-stone hover:text-on-dark transition-colors">
              Cancelar
            </button>
            <button type="submit" disabled={saving}
              className="px-lg py-sm rounded-md text-body-sm bg-primary text-on-primary hover:bg-primary/90 disabled:opacity-50 transition-colors">
              {saving ? "Guardando..." : "Guardar"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
