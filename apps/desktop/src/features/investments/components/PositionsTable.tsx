import { formatCurrency } from "@/lib/formatters/currency";
import type { HoldingEnriched } from "@/lib/types";
import PositionMenu, { type MenuItem } from "./PositionMenu";

interface Props {
  holdings: HoldingEnriched[];
  accountNames: Record<string, string>;
  mergeableIds: Set<string>;
  onAddStock: () => void;
  onAddFund: () => void;
  onEdit: (h: HoldingEnriched) => void;
  onDelete: (h: HoldingEnriched) => void;
  onMerge: (h: HoldingEnriched) => void;
  onHistory: (h: HoldingEnriched) => void;
  onFundValue: (h: HoldingEnriched) => void;
}

const TYPE_LABEL: Record<string, string> = {
  stock: "Acción", etf: "ETF", fund: "Fondo", crypto: "Cripto", bond: "Bono", cash: "Efectivo",
};

// Estado alineado con la clasificación de Calidad: fondos manuales, resto por precio.
function estado(h: HoldingEnriched): { label: string; cls: string } {
  if (h.is_mock) return { label: "Demo", cls: "bg-amber-400/15 text-amber-300" };
  if (h.asset_type === "fund") return { label: "Manual", cls: "bg-[var(--bg-interactive)] text-stone" };
  if (h.market_value === null) return { label: "Sin precio", cls: "bg-amber-400/15 text-amber-300" };
  return { label: "Confirmado", cls: "bg-accent-teal/15 text-accent-teal" };
}

export default function PositionsTable({
  holdings, accountNames, mergeableIds,
  onAddStock, onAddFund, onEdit, onDelete, onMerge, onHistory, onFundValue,
}: Props) {
  const total = holdings.reduce((s, h) => s + Number(h.market_value ?? 0), 0);

  const th = (label: string, right = false) => (
    <th className={`px-3 py-2.5 text-[11px] font-medium uppercase tracking-wide text-stone ${right ? "text-right" : "text-left"}`}>
      {label}
    </th>
  );

  return (
    <div className="bg-surface-card border border-hairline-dark rounded-md p-xl">
      <div className="flex items-center justify-between mb-md gap-md flex-wrap">
        <p className="text-body-sm text-on-dark">Posiciones ({holdings.length})</p>
        <div className="flex gap-sm">
          <button onClick={onAddStock} className="mercury-button rounded-lg px-md py-xs text-caption">+ Acción</button>
          <button onClick={onAddFund} className="mercury-button rounded-lg px-md py-xs text-caption">+ Fondo</button>
        </div>
      </div>

      {holdings.length === 0 ? (
        <p className="text-caption text-stone py-md text-center">Sin posiciones todavía.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/8">
                {th("Nombre")}{th("Broker")}{th("Divisa")}{th("Tipo")}
                {th("Peso", true)}{th("Valor EUR", true)}{th("P&L %", true)}{th("Estado")}
                <th className="px-3 py-2.5" />
              </tr>
            </thead>
            <tbody>
              {holdings.map((h) => {
                const value = Number(h.market_value ?? 0);
                const weight = total > 0 ? (value / total) * 100 : 0;
                const pct = h.return_percent;
                const positive = pct !== null && pct >= 0;
                const st = estado(h);
                const isFund = h.asset_type === "fund";

                const items: MenuItem[] = [{ label: "Editar", onClick: () => onEdit(h) }];
                if (isFund) items.push({ label: "Actualizar valor", onClick: () => onFundValue(h) });
                else items.push({ label: "Historial", onClick: () => onHistory(h) });
                if (mergeableIds.has(h.id)) items.push({ label: "Fusionar duplicado", onClick: () => onMerge(h) });
                items.push({ label: "Eliminar", onClick: () => onDelete(h), danger: true });

                return (
                  <tr key={h.id} className="border-b border-white/4 hover:bg-[var(--bg-interactive)] transition-colors">
                    <td className="px-3 py-3 font-medium text-on-dark">
                      {h.display_name}
                      {h.symbol && <span className="ml-1.5 text-[11px] text-stone">{h.symbol}</span>}
                    </td>
                    <td className="px-3 py-3 text-stone">{accountNames[h.account_id] ?? h.broker}</td>
                    <td className="px-3 py-3 text-stone">{h.currency}</td>
                    <td className="px-3 py-3 text-stone">{TYPE_LABEL[h.asset_type] ?? h.asset_type}</td>
                    <td className="px-3 py-3 text-right text-on-dark">{weight.toFixed(1)}%</td>
                    <td className="px-3 py-3 text-right text-on-dark">
                      {h.market_value ? formatCurrency(h.market_value) : "—"}
                    </td>
                    <td className={`px-3 py-3 text-right font-medium ${pct === null ? "text-stone" : positive ? "text-accent-teal" : "text-accent-danger"}`}>
                      {pct === null ? "—" : `${positive ? "+" : ""}${pct.toFixed(1)}%`}
                    </td>
                    <td className="px-3 py-3">
                      <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${st.cls}`}>{st.label}</span>
                    </td>
                    <td className="px-3 py-3 text-right">
                      <PositionMenu items={items} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
