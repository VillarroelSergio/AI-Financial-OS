import { useEffect, useState } from "react";
import { X } from "lucide-react";
import {
  addFundSnapshot, deleteFundSnapshot, getFundSnapshots, updateFundSnapshot,
  type FundValuationSnapshot,
} from "@/lib/api/investments";
import { formatCurrency } from "@/lib/formatters/currency";
import type { HoldingEnriched } from "@/lib/types";
import PositionEvolutionChart from "@/features/investments/tracking/PositionEvolutionChart";

interface FundValuationDialogProps {
  holding: HoldingEnriched | null;
  onClose: () => void;
  onChanged: () => void;
}

const today = () => new Date().toISOString().slice(0, 10);

export default function FundValuationDialog({ holding, onClose, onChanged }: FundValuationDialogProps) {
  const [snapshots, setSnapshots] = useState<FundValuationSnapshot[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newValue, setNewValue] = useState("");
  const [newDate, setNewDate] = useState(today());
  const [chartKey, setChartKey] = useState(0);

  useEffect(() => {
    if (!holding) return;
    setError(null);
    setNewValue("");
    setNewDate(today());
    setLoading(true);
    getFundSnapshots(holding.id)
      .then(setSnapshots)
      .catch((err) => setError(err instanceof Error ? err.message : "Error al cargar las valoraciones"))
      .finally(() => setLoading(false));
  }, [holding]);

  if (!holding) return null;

  const afterChange = async () => {
    await getFundSnapshots(holding.id).then(setSnapshots);
    setChartKey((k) => k + 1);
    onChanged();
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await addFundSnapshot(holding.id, {
        date: newDate,
        market_value: newValue,
        currency: holding.currency,
      });
      setNewValue("");
      await afterChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    }
  };

  const handleEditValue = async (snap: FundValuationSnapshot, value: string) => {
    if (!value || value === snap.market_value) return;
    try {
      await updateFundSnapshot(snap.id, { market_value: value });
      await afterChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    }
  };

  const handleDelete = async (snap: FundValuationSnapshot) => {
    try {
      await deleteFundSnapshot(snap.id);
      await afterChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al borrar");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-2xl rounded-xl border border-hairline-dark bg-surface-elevated p-2xl">
        <div className="flex items-center justify-between mb-lg">
          <div>
            <h2 className="text-heading-sm text-on-dark">Actualizar valor · {holding.display_name}</h2>
            <p className="text-caption text-stone">
              Valor actual: {holding.market_value ? formatCurrency(holding.market_value) : "sin valorar"}
            </p>
          </div>
          <button onClick={onClose} className="text-stone hover:text-on-dark" aria-label="Cerrar">
            <X size={18} />
          </button>
        </div>

        {snapshots.length > 0 && (
          <div className="mb-lg">
            <PositionEvolutionChart key={chartKey} holdingId={holding.id} />
          </div>
        )}

        <form onSubmit={handleAdd} className="flex items-end gap-md mb-lg">
          <div className="flex-1">
            <label className="text-caption text-stone block mb-xs">Valor del fondo ({holding.currency})</label>
            <input
              type="number" step="0.01" min="0" required
              className="w-full bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
              value={newValue} onChange={(e) => setNewValue(e.target.value)}
            />
          </div>
          <div>
            <label className="text-caption text-stone block mb-xs">Fecha</label>
            <input
              type="date" required
              className="bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
              value={newDate} onChange={(e) => setNewDate(e.target.value)}
            />
          </div>
          <button type="submit" className="px-lg py-sm rounded-md text-body-sm bg-primary text-on-primary hover:bg-primary/90">
            Guardar
          </button>
        </form>

        {error && <p className="text-caption text-accent-danger mb-md">{error}</p>}

        <div className="max-h-64 overflow-y-auto divide-y divide-hairline-dark">
          {loading ? (
            <p className="text-caption text-stone py-md">Cargando...</p>
          ) : snapshots.length === 0 ? (
            <p className="text-caption text-stone py-md">Sin valoraciones todavía. Añade la primera para ver su evolución.</p>
          ) : (
            snapshots.map((snap) => (
              <div key={snap.id} className="flex items-center gap-md py-sm">
                <span className="text-caption text-stone w-24 shrink-0">
                  {new Date(`${snap.date}T00:00:00`).toLocaleDateString("es-ES")}
                </span>
                <input
                  type="number" step="0.01"
                  className="flex-1 bg-canvas-dark border border-hairline-dark rounded-md px-md py-xs text-body-sm text-on-dark focus:outline-none focus:border-primary"
                  defaultValue={snap.market_value}
                  onBlur={(e) => handleEditValue(snap, e.target.value)}
                />
                <span className="text-caption text-mute w-16 shrink-0">{snap.source}</span>
                <button onClick={() => handleDelete(snap)} className="text-caption text-stone hover:text-accent-danger shrink-0">
                  Borrar
                </button>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
