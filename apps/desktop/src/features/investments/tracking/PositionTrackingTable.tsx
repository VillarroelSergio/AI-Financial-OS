import { Fragment, useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import type { HoldingEnriched } from "@/lib/types";
import PositionEvolutionChart from "./PositionEvolutionChart";

function formatPrice(price: string | number | null, currency: string): string {
  if (price === null) return "—";
  const n = Number(price);
  if (!n) return "—";
  return `${n.toFixed(2)} ${currency}`.trim();
}

function formatDate(iso: string | null): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("es-ES", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const HEADERS = ["", "Activo", "Ticker", "Precio entrada", "Precio actual", "Evolución", "Valor de mercado", "Última act."];

interface Props {
  holdings: HoldingEnriched[];
}

export default function PositionTrackingTable({ holdings }: Props) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <div className="overflow-x-auto rounded-xl border border-hairline-dark">
      <table className="w-full text-sm text-left">
        <thead>
          <tr className="border-b border-hairline-dark bg-surface-deep">
            {HEADERS.map((h, i) => (
              <th
                key={i}
                className="px-4 py-3 text-[11px] font-medium text-mute uppercase tracking-wide whitespace-nowrap"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {holdings.map((h) => {
            const expanded = expandedId === h.id;
            const pct = h.unrealized_pnl_pct;
            const positive = pct >= 0;
            return (
              <Fragment key={h.id}>
                <tr
                  onClick={() => setExpandedId(expanded ? null : h.id)}
                  className="border-b border-hairline-dark last:border-0 hover:bg-white/[.02] transition-colors cursor-pointer"
                >
                  <td className="pl-4 py-3 w-6 text-stone">
                    {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                  </td>
                  <td className="px-4 py-3 font-medium text-on-dark whitespace-nowrap">
                    {h.display_name}
                    <div className="text-[10px] text-mute mt-0.5">{h.broker}</div>
                  </td>
                  <td className="px-4 py-3 text-stone font-mono text-xs">{h.symbol}</td>
                  <td className="px-4 py-3 text-on-dark font-mono">
                    {formatPrice(h.average_price, h.currency)}
                  </td>
                  <td className="px-4 py-3 text-on-dark font-mono">
                    {formatPrice(h.current_price, h.current_price_currency)}
                  </td>
                  <td className="px-4 py-3 font-mono">
                    <span className={positive ? "text-emerald-400" : "text-red-400"}>
                      {positive ? "+" : ""}
                      {pct.toFixed(2)}%
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-on-dark">
                    {h.market_value !== null ? `${Number(h.market_value).toFixed(2)} EUR` : "—"}
                  </td>
                  <td className="px-4 py-3 text-stone text-xs">{formatDate(h.current_price_updated_at)}</td>
                </tr>
                {expanded && (
                  <tr className="border-b border-hairline-dark last:border-0">
                    <td colSpan={HEADERS.length} className="px-6 py-4 bg-black/20">
                      <PositionEvolutionChart holdingId={h.id} />
                    </td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
