import { useState } from "react";
import { createFund } from "@/lib/api/investments";
import { formatCurrency } from "@/lib/formatters/currency";
import type { Account } from "@/lib/types";
import InvestmentAccountPicker from "./InvestmentAccountPicker";

interface AddFundDialogProps {
  open: boolean;
  accountId: string;
  accounts: Account[];
  onClose: () => void;
  onSuccess: () => void;
}

type Mode = "return" | "units";

const today = () => new Date().toISOString().slice(0, 10);

export default function AddFundDialog({ open, accounts, onClose, onSuccess }: AddFundDialogProps) {
  const [mode, setMode] = useState<Mode>("return");
  const [account, setAccount] = useState("");
  const [name, setName] = useState("");
  const [returnPct, setReturnPct] = useState("");
  const [reportedGain, setReportedGain] = useState("");
  const [value, setValue] = useState("");     // valor actual (vía rendimiento)
  const [units, setUnits] = useState("");     // nº participaciones (vía participaciones)
  const [nav, setNav] = useState("");         // valor liquidativo (vía participaciones)
  const [date, setDate] = useState(today());
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  const reset = () => {
    setMode("return"); setAccount("");
    setName(""); setReturnPct(""); setReportedGain(""); setValue("");
    setUnits(""); setNav(""); setDate(today()); setError(null);
  };
  const handleClose = () => { reset(); onClose(); };

  // Valor actual: directo (rendimiento) o nº × valor liquidativo (participaciones).
  const u = parseFloat(units), n = parseFloat(nav);
  const currentValue = mode === "return"
    ? parseFloat(value)
    : (Number.isFinite(u) && Number.isFinite(n) ? u * n : NaN);

  // La rentabilidad reportada por plataformas como Finizens puede ser TWR/MWR y
  // no tiene por qué cuadrar con la ganancia simple. Si existe ganancia en euros,
  // esta es la fuente fiable para derivar lo aportado.
  const pct = parseFloat(returnPct);
  const gainInput = parseFloat(reportedGain);
  const factor = 1 + (Number.isFinite(pct) ? pct : 0) / 100;
  const contributed = Number.isFinite(currentValue) && Number.isFinite(gainInput)
    ? currentValue - gainInput
    : (factor > 0 && Number.isFinite(currentValue) ? currentValue / factor : NaN);
  const gain = Number.isFinite(currentValue) && Number.isFinite(contributed)
    ? currentValue - contributed
    : null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!Number.isFinite(currentValue) || currentValue <= 0) {
      setError(mode === "return" ? "Introduce un valor actual válido" : "Introduce nº de participaciones y valor liquidativo");
      return;
    }
    if (factor <= 0) { setError("El % de rendimiento no puede ser ≤ −100%"); return; }
    if (!Number.isFinite(contributed) || contributed <= 0) {
      setError("La ganancia no puede ser igual o superior al valor actual");
      return;
    }
    if (!account) { setError("Selecciona una cuenta"); return; }
    setSaving(true);
    setError(null);
    try {
      await createFund({
        name, account_id: account,
        contributed: contributed.toFixed(2), value: currentValue.toFixed(2), date,
        units: mode === "units" ? u.toString() : null,
        nav: mode === "units" ? n.toString() : null,
        reported_return_pct: Number.isFinite(pct) ? pct.toString() : null,
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
          <InvestmentAccountPicker accounts={accounts} value={account} onChange={setAccount} />
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
              <label className="text-caption text-stone block mb-xs">Rentabilidad reportada (%)</label>
              <input type="number" step="0.01" className={inputCls} value={returnPct}
                onChange={e => setReturnPct(e.target.value)} placeholder="8.50" />
            </div>
            <div>
              <label className="text-caption text-stone block mb-xs">Ganancia reportada (EUR)</label>
              <input type="number" step="0.01" className={inputCls} value={reportedGain}
                onChange={e => setReportedGain(e.target.value)} placeholder="264.66" />
            </div>
          </div>

          <div>
            <label className="text-caption text-stone block mb-xs">Fecha de valoración</label>
            <input type="date" required className={inputCls} value={date}
              onChange={e => setDate(e.target.value)} />
          </div>

          {Number.isFinite(currentValue) && (
            <div className="rounded-md bg-canvas-dark border border-hairline-dark px-md py-sm space-y-xs">
              <div className="flex justify-between text-caption">
                <span className="text-stone">Valor actual</span>
                <span className="text-on-dark">{formatCurrency(currentValue.toFixed(2))}</span>
              </div>
              <div className="flex justify-between text-caption">
                <span className="text-stone">Aportado {Number.isFinite(gainInput) ? "(desde ganancia)" : "(estimado)"}</span>
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
            {Number.isFinite(gainInput) && Number.isFinite(pct) && " La ganancia y la rentabilidad reportadas se conservan por separado."}
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
