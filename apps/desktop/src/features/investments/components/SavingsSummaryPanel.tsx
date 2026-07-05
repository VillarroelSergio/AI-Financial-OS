import { useEffect, useState } from "react";
import { getSavingsProjection, type SavingsProjection } from "@/lib/api/investments";
import { formatCurrency } from "@/lib/formatters/currency";
import type { HoldingEnriched } from "@/lib/types";
import PositionMenu, { type MenuItem } from "./PositionMenu";

interface Props {
  holdings: HoldingEnriched[];
  onAddSavings: () => void;
  onEdit: (h: HoldingEnriched) => void;
  onDelete: (h: HoldingEnriched) => void;
  onDetail: (h: HoldingEnriched) => void;
}

// Saldo promedio = media del saldo a fin de cada mes del calendario (tipo Trade Republic).
function avgBalance(p: SavingsProjection): number {
  if (p.points.length === 0) return Number(p.current_balance);
  const sum = p.points.reduce((s, m) => s + Number(m.balance_end), 0);
  return sum / p.points.length;
}

function SavingsRow({ h, onEdit, onDelete, onDetail }: {
  h: HoldingEnriched; onEdit: (h: HoldingEnriched) => void;
  onDelete: (h: HoldingEnriched) => void; onDetail: (h: HoldingEnriched) => void;
}) {
  const [proj, setProj] = useState<SavingsProjection | null>(null);

  useEffect(() => {
    let alive = true;
    getSavingsProjection(h.account_id)
      .then((p) => { if (alive) setProj(p); })
      .catch(() => { if (alive) setProj(null); });
    return () => { alive = false; };
  }, [h.account_id]);

  const rate = proj?.current_rate != null ? `${Number(proj.current_rate).toFixed(2)}%` : "—";
  const avg = proj ? formatCurrency(avgBalance(proj).toFixed(2)) : "—";
  const total = proj ? formatCurrency(proj.total_interest) : "—";
  const balance = proj ? formatCurrency(proj.current_balance) : (h.market_value ? formatCurrency(h.market_value) : "—");

  const items: MenuItem[] = [
    { label: "Evolución", onClick: () => onDetail(h) },
    { label: "Editar", onClick: () => onEdit(h) },
    { label: "Eliminar", onClick: () => onDelete(h), danger: true },
  ];

  const metric = (label: string, value: string, cls = "text-on-dark") => (
    <div>
      <p className="text-caption text-stone">{label}</p>
      <p className={`text-body-sm ${cls}`}>{value}</p>
    </div>
  );

  return (
    <div className="flex items-center justify-between gap-md py-md">
      <div className="min-w-0 flex-1">
        <button onClick={() => onDetail(h)} className="text-body-sm text-on-dark truncate hover:text-primary transition-colors text-left">
          {h.display_name}
        </button>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-md mt-sm">
          {metric("Interés anual", rate)}
          {metric("Saldo promedio", avg)}
          {metric("Total obtenido", total, "text-accent-teal")}
          {metric("Saldo actual", balance)}
        </div>
      </div>
      <PositionMenu items={items} />
    </div>
  );
}

export default function SavingsSummaryPanel({ holdings, onAddSavings, onEdit, onDelete, onDetail }: Props) {
  return (
    <div className="bg-surface-card border border-hairline-dark rounded-md p-xl">
      <div className="flex items-center justify-between mb-sm gap-md">
        <p className="text-body-sm text-on-dark">Cuentas remuneradas</p>
        <button onClick={onAddSavings} className="mercury-button rounded-lg px-md py-xs text-caption">+ Cuenta de ahorro</button>
      </div>
      {holdings.length === 0 ? (
        <p className="text-caption text-stone py-md text-center">Sin cuentas remuneradas todavía.</p>
      ) : (
        <div className="divide-y divide-hairline-dark">
          {holdings.map((h) => (
            <SavingsRow key={h.id} h={h} onEdit={onEdit} onDelete={onDelete} onDetail={onDetail} />
          ))}
        </div>
      )}
    </div>
  );
}
