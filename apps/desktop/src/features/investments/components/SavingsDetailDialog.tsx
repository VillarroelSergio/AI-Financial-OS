import { useEffect, useState } from "react";
import { X } from "lucide-react";
import { getSavingsProjection, type SavingsProjection } from "@/lib/api/investments";
import { formatCurrency } from "@/lib/formatters/currency";
import type { HoldingEnriched } from "@/lib/types";
import SavingsScheduleChart from "./SavingsScheduleChart";

interface Props {
  holding: HoldingEnriched | null;
  onClose: () => void;
}

export default function SavingsDetailDialog({ holding, onClose }: Props) {
  const [schedule, setSchedule] = useState<SavingsProjection | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!holding) return;
    setSchedule(null);
    setError(null);
    getSavingsProjection(holding.account_id)
      .then(setSchedule)
      .catch((e) => setError(e instanceof Error ? e.message : "No se pudo calcular el interés"));
  }, [holding]);

  if (!holding) return null;

  const currentRate = schedule?.current_rate ? `${Number(schedule.current_rate).toFixed(2)}%` : "—";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
      <div className="w-full max-w-2xl rounded-xl border border-hairline-dark bg-surface-elevated p-2xl">
        <div className="flex items-center justify-between mb-lg">
          <h2 className="text-heading-sm text-on-dark">Evolución · {holding.display_name}</h2>
          <button onClick={onClose} className="text-stone hover:text-on-dark" aria-label="Cerrar">
            <X size={18} />
          </button>
        </div>

        {error && <p className="text-caption text-accent-danger py-md">{error}</p>}

        {schedule && (
          <>
            <div className="grid grid-cols-3 gap-lg mb-lg">
              <div>
                <p className="text-caption text-stone">Saldo actual</p>
                <p className="text-body text-on-dark">{formatCurrency(schedule.current_balance)}</p>
              </div>
              <div>
                <p className="text-caption text-stone">Intereses totales</p>
                <p className="text-body text-accent-teal">+{formatCurrency(schedule.total_interest)}</p>
              </div>
              <div>
                <p className="text-caption text-stone">Tipo vigente</p>
                <p className="text-body text-on-dark">{currentRate}</p>
              </div>
            </div>
            {schedule.points.length > 0 ? (
              <SavingsScheduleChart schedule={schedule} />
            ) : (
              <p className="text-caption text-stone py-md">Sin meses calculados todavía.</p>
            )}
            {schedule.estimated && (
              <p className="text-caption text-mute mt-sm">
                Estimación: saldo inicial retro-calculado desde el saldo actual asumiendo sin movimientos. Añade movimientos para afinar.
              </p>
            )}
          </>
        )}
      </div>
    </div>
  );
}
