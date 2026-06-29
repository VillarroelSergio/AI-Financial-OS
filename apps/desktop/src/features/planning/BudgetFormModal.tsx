import { useState } from "react";
import { X } from "lucide-react";
import type { BudgetCreate } from "@/lib/api/budgets";

interface Props {
  onSubmit: (data: BudgetCreate) => Promise<void>;
  onClose: () => void;
}

export default function BudgetFormModal({ onSubmit, onClose }: Props) {
  const [categoryId, setCategoryId] = useState("");
  const [amount, setAmount] = useState("");
  const [threshold, setThreshold] = useState("80");
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!categoryId || !amount) return;
    setSaving(true);
    try {
      await onSubmit({ category_id: categoryId, amount: parseFloat(amount), alert_threshold_pct: parseInt(threshold) });
      onClose();
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-md rounded-2xl bg-surface-elevated p-6 space-y-5">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold text-on-dark">Nuevo presupuesto</h3>
          <button onClick={onClose} className="text-stone hover:text-on-dark"><X size={18} /></button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs text-stone">ID de categoría</label>
            <input
              value={categoryId}
              onChange={e => setCategoryId(e.target.value)}
              placeholder="ej. cat-alimentacion"
              className="w-full rounded-lg bg-white/5 px-3 py-2.5 text-sm text-on-dark placeholder:text-stone focus:outline-none focus:ring-1 focus:ring-primary"
              required
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs text-stone">Importe mensual (€)</label>
            <input
              type="number"
              value={amount}
              onChange={e => setAmount(e.target.value)}
              placeholder="500"
              min="1"
              step="0.01"
              className="w-full rounded-lg bg-white/5 px-3 py-2.5 text-sm text-on-dark placeholder:text-stone focus:outline-none focus:ring-1 focus:ring-primary"
              required
            />
          </div>

          <div className="space-y-1.5">
            <label className="text-xs text-stone">Alerta al {threshold}% del límite</label>
            <input
              type="range" min="50" max="100" step="5"
              value={threshold}
              onChange={e => setThreshold(e.target.value)}
              className="w-full accent-primary"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="flex-1 rounded-lg bg-white/5 py-2.5 text-sm text-stone hover:text-on-dark transition-colors">
              Cancelar
            </button>
            <button type="submit" disabled={saving} className="flex-1 rounded-lg bg-primary py-2.5 text-sm font-medium text-white transition-colors disabled:opacity-50">
              {saving ? "Guardando..." : "Crear presupuesto"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
