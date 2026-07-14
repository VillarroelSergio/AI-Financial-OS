import { ArrowUpDown } from "lucide-react";
import { useState } from "react";
import type { ReconciliationHolding } from "@/lib/api/investments";
import QualityStateBadge from "./QualityStateBadge";

type SortKey = "display_name" | "weight_pct" | "value_eur" | "unrealized_pnl_pct";

interface Props {
  holdings: ReconciliationHolding[];
}

export default function ReconciliationTable({ holdings }: Props) {
  const [sortKey, setSortKey] = useState<SortKey>("weight_pct");
  const [asc, setAsc] = useState(false);

  const sorted = [...holdings].sort((a, b) => {
    const va = a[sortKey];
    const vb = b[sortKey];
    const cmp = typeof va === "string" ? va.localeCompare(vb as string) : (va as number) - (vb as number);
    return asc ? cmp : -cmp;
  });

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setAsc((p) => !p);
    else { setSortKey(key); setAsc(false); }
  };

  const th = (label: string, key?: SortKey) => (
    <th
      className={["px-3 py-2.5 text-left text-[11px] font-medium uppercase tracking-wide text-stone select-none", key ? "cursor-pointer hover:text-on-dark" : ""].join(" ")}
      onClick={key ? () => toggleSort(key) : undefined}
    >
      <span className="inline-flex items-center gap-1">
        {label}
        {key && <ArrowUpDown size={11} className={sortKey === key ? "text-primary" : "text-stone/50"} />}
      </span>
    </th>
  );

  if (holdings.length === 0) {
    return <p className="py-12 text-center text-sm text-stone">No hay posiciones para mostrar.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-white/8">
            {th("Nombre", "display_name")}
            {th("Broker")}
            {th("Divisa")}
            {th("Tipo")}
            {th("Peso", "weight_pct")}
            {th("Valor EUR", "value_eur")}
            {th("P&L %", "unrealized_pnl_pct")}
            {th("Estado")}
          </tr>
        </thead>
        <tbody>
          {sorted.map((h) => {
            const pnlPositive = h.unrealized_pnl_pct >= 0;
            return (
              <tr key={h.holding_id} className="border-b border-white/4 hover:bg-[var(--bg-interactive)] transition-colors">
                <td className="px-3 py-3 font-medium text-on-dark">
                  {h.display_name}
                  {h.ticker && <span className="ml-1.5 text-[11px] text-stone">{h.ticker}</span>}
                </td>
                <td className="px-3 py-3 text-stone">{h.broker}</td>
                <td className="px-3 py-3 text-stone">{h.currency}</td>
                <td className="px-3 py-3 text-stone capitalize">{h.asset_type}</td>
                <td className="px-3 py-3 text-on-dark">{h.weight_pct.toFixed(1)}%</td>
                <td className="px-3 py-3 text-on-dark">
                  {h.value_eur.toLocaleString("es-ES", { style: "currency", currency: "EUR", maximumFractionDigits: 0 })}
                </td>
                <td className={["px-3 py-3 font-medium", pnlPositive ? "text-accent-teal" : "text-accent-danger"].join(" ")}>
                  {pnlPositive ? "+" : ""}{h.unrealized_pnl_pct.toFixed(1)}%
                </td>
                <td className="px-3 py-3">
                  <QualityStateBadge state={h.quality_state} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
