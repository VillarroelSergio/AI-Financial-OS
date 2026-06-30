import { useState } from "react";
import { X } from "lucide-react";
import type { RecurringCreate } from "@/lib/api/budgets";

interface Props {
  onSubmit: (data: RecurringCreate) => Promise<void>;
  onClose: () => void;
}

export default function RecurringFormModal({ onSubmit, onClose }: Props) {
  const [name, setName] = useState("");
  const [amount, setAmount] = useState("");
  const [type, setType] = useState<"income" | "expense">("expense");
  const [frequency, setFrequency] = useState<"monthly" | "weekly" | "yearly">("monthly");
  const [nextDate, setNextDate] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name || !amount || !nextDate) return;
    setSaving(true);
    try {
      await onSubmit({ name, amount: parseFloat(amount), type, frequency, next_date: nextDate });
      onClose();
    } finally {
      setSaving(false);
    }
  };

  const inputClass = "w-full rounded-lg bg-white/5 px-3 py-2.5 text-sm text-on-dark focus:outline-none focus:ring-1 focus:ring-primary";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-md rounded-2xl bg-surface-elevated p-6 space-y-5">
        <div className="flex items-center justify-between">
          <h3 className="text-base font-semibold text-on-dark">Añadir recurrente</h3>
          <button onClick={onClose} className="text-stone hover:text-on-dark"><X size={18} /></button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <input value={name} onChange={e => setName(e.target.value)} placeholder="Nombre (ej. Netflix)" className={inputClass} required />

          <div className="grid grid-cols-2 gap-3">
            <select value={type} onChange={e => setType(e.target.value as "income" | "expense")} className={inputClass}>
              <option value="expense">Gasto</option>
              <option value="income">Ingreso</option>
            </select>
            <select value={frequency} onChange={e => setFrequency(e.target.value as "monthly" | "weekly" | "yearly")} className={inputClass}>
              <option value="monthly">Mensual</option>
              <option value="weekly">Semanal</option>
              <option value="yearly">Anual</option>
            </select>
          </div>

          <input type="number" value={amount} onChange={e => setAmount(e.target.value)} placeholder="Importe (€)" min="0.01" step="0.01" className={inputClass} required />
          <input type="date" value={nextDate} onChange={e => setNextDate(e.target.value)} className={inputClass} required />

          <div className="flex gap-3 pt-2">
            <button type="button" onClick={onClose} className="flex-1 rounded-lg bg-white/5 py-2.5 text-sm text-stone hover:text-on-dark">Cancelar</button>
            <button type="submit" disabled={saving} className="flex-1 rounded-lg bg-primary py-2.5 text-sm font-medium text-white disabled:opacity-50">
              {saving ? "Guardando..." : "Añadir"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
