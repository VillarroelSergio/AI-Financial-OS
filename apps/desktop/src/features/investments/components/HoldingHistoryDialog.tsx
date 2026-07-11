import { useEffect, useState } from "react";
import { X } from "lucide-react";
import {
  addHoldingHistory, deleteHoldingHistory, getHoldingHistory, updateHoldingHistory,
  type HoldingValueHistoryEntry,
} from "@/lib/api/investments";
import type { HoldingEnriched } from "@/lib/types";

interface HoldingHistoryDialogProps {
  holding: HoldingEnriched | null;
  onClose: () => void;
  onChanged: () => void;
}

export default function HoldingHistoryDialog({ holding, onClose, onChanged }: HoldingHistoryDialogProps) {
  const [entries, setEntries] = useState<HoldingValueHistoryEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [newPrice, setNewPrice] = useState("");
  const [newDate, setNewDate] = useState("");

  useEffect(() => {
    if (!holding) return;
    setError(null);
    setNewPrice("");
    setNewDate("");
    setLoading(true);
    getHoldingHistory(holding.id)
      .then(setEntries)
      .catch((err) => setError(err instanceof Error ? err.message : "Error al cargar el historial"))
      .finally(() => setLoading(false));
  }, [holding]);

  if (!holding) return null;

  const refresh = () => getHoldingHistory(holding.id).then(setEntries);

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await addHoldingHistory(holding.id, {
        price: newPrice,
        currency: holding.currency,
        recorded_at: newDate ? new Date(newDate).toISOString() : undefined,
      });
      setNewPrice("");
      setNewDate("");
      await refresh();
      onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    }
  };

  const handleEditPrice = async (entry: HoldingValueHistoryEntry, price: string) => {
    if (!price || price === entry.price) return;
    try {
      await updateHoldingHistory(holding.id, entry.id, { price });
      await refresh();
      onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al guardar");
    }
  };

  const handleDelete = async (entry: HoldingValueHistoryEntry) => {
    try {
      await deleteHoldingHistory(holding.id, entry.id);
      await refresh();
      onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al borrar");
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-lg rounded-xl border border-hairline-dark bg-surface-elevated p-2xl">
        <div className="flex items-center justify-between mb-lg">
          <h2 className="text-heading-sm text-on-dark">Historial · {holding.display_name}</h2>
          <button onClick={onClose} className="text-stone hover:text-on-dark" aria-label="Cerrar">
            <X size={18} />
          </button>
        </div>

        <form onSubmit={handleAdd} className="flex items-end gap-md mb-lg">
          <div className="flex-1">
            <label className="text-caption text-stone block mb-xs">Nuevo valor ({holding.currency})</label>
            <input
              type="number" step="0.0001" min="0" required
              className="w-full bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
              value={newPrice} onChange={(e) => setNewPrice(e.target.value)}
            />
          </div>
          <div>
            <label className="text-caption text-stone block mb-xs">Fecha (opcional)</label>
            <input
              type="date"
              className="bg-canvas-dark border border-hairline-dark rounded-md px-md py-sm text-body-sm text-on-dark focus:outline-none focus:border-primary"
              value={newDate} onChange={(e) => setNewDate(e.target.value)}
            />
          </div>
          <button type="submit" className="px-lg py-sm rounded-md text-body-sm bg-primary text-on-primary hover:bg-primary/90">
            Añadir
          </button>
        </form>

        {error && <p className="text-caption text-accent-danger mb-md">{error}</p>}

        <div className="max-h-80 overflow-y-auto divide-y divide-hairline-dark">
          {loading ? (
            <p className="text-caption text-stone py-md">Cargando...</p>
          ) : entries.length === 0 ? (
            <p className="text-caption text-stone py-md">Sin entradas todavía.</p>
          ) : (
            entries.map((entry) => (
              <div key={entry.id} className="flex items-center gap-md py-sm">
                <span className="text-caption text-stone w-24 shrink-0">
                  {new Date(entry.recorded_at).toLocaleDateString("es-ES")}
                </span>
                <input
                  type="number" step="0.0001"
                  className="flex-1 bg-canvas-dark border border-hairline-dark rounded-md px-md py-xs text-body-sm text-on-dark focus:outline-none focus:border-primary"
                  defaultValue={entry.price}
                  onBlur={(e) => handleEditPrice(entry, e.target.value)}
                />
                <span className="text-caption text-mute w-16 shrink-0">{entry.source}</span>
                <button onClick={() => handleDelete(entry)} className="text-caption text-stone hover:text-accent-danger shrink-0">
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
