import { useState } from "react";
import { Trash2, AlertCircle } from "lucide-react";
import type { ReviewRow } from "@/lib/types/portfolio-import";
import ImportStatusBadge from "./ImportStatusBadge";

function fmt(n: number | null, decimals = 2): string {
  if (n === null) return "—";
  return n.toLocaleString("es-ES", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

interface EditableCellProps {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  className?: string;
  mono?: boolean;
}

function EditableCell({ value, onChange, placeholder, className = "", mono = false }: EditableCellProps) {
  return (
    <input
      className={`w-full bg-transparent border-b border-transparent focus:border-primary outline-none text-sm py-0.5
        ${mono ? "font-mono" : ""} ${className}`}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder ?? "—"}
    />
  );
}

interface Props {
  rows: ReviewRow[];
  accountId: string;
  onUpdate: (id: string, patch: Partial<ReviewRow>) => void;
  onDiscard: (id: string) => void;
  onMarkManual: (id: string) => void;
}

const HEADERS = [
  "Activo",
  "Ticker",
  "Mercado",
  "Divisa",
  "Cantidad",
  "Valor capturado",
  "Rentab. capturada",
  "Coste estimado",
  "Estado",
  "",
];

export default function ImportReviewTable({
  rows,
  onUpdate,
  onDiscard,
  onMarkManual,
}: Props) {
  const [expandedId, setExpandedId] = useState<string | null>(null);

  const activeRows = rows.filter((r) => r.review_state !== "discarded");

  if (activeRows.length === 0) {
    return (
      <p className="text-sm text-mute text-center py-8">
        No hay posiciones pendientes de revisión.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto rounded-xl border border-hairline-dark">
      <table className="w-full text-sm text-left">
        <thead>
          <tr className="border-b border-hairline-dark bg-surface-deep">
            {HEADERS.map((h) => (
              <th
                key={h}
                className="px-4 py-3 text-[11px] font-medium text-mute uppercase tracking-wide whitespace-nowrap"
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {activeRows.map((row) => {
            const isExpanded = expandedId === row.id;
            const effectiveTicker = row.override_ticker ?? row.selected_ticker;
            const effectiveCurrency = row.override_currency ?? row.currency;
            const effectiveQty = row.override_quantity ?? row.quantity;
            const showCostWarning = row.is_cost_estimated && row.estimated_cost !== null;

            return (
              <>
                <tr
                  key={row.id}
                  className="border-b border-hairline-dark last:border-0 hover:bg-white/[.02] transition-colors cursor-pointer"
                  onClick={() => setExpandedId(isExpanded ? null : row.id)}
                >
                  {/* Activo */}
                  <td className="px-4 py-3">
                    <div className="font-medium text-on-dark">{row.raw_name}</div>
                    {row.notes.length > 0 && (
                      <div className="text-[10px] text-amber-400/80 mt-0.5 flex items-start gap-1">
                        <AlertCircle size={10} className="mt-0.5 shrink-0" />
                        <span className="leading-tight">{row.notes[0]}</span>
                      </div>
                    )}
                  </td>

                  {/* Ticker */}
                  <td className="px-4 py-3 font-mono text-xs text-stone" onClick={(e) => e.stopPropagation()}>
                    <EditableCell
                      mono
                      value={row.override_ticker ?? effectiveTicker ?? ""}
                      onChange={(v) => onUpdate(row.id, { override_ticker: v || null })}
                      placeholder="ticker"
                      className="text-stone"
                    />
                  </td>

                  {/* Mercado */}
                  <td className="px-4 py-3 text-stone text-xs">{row.exchange ?? "—"}</td>

                  {/* Divisa */}
                  <td className="px-4 py-3 text-xs" onClick={(e) => e.stopPropagation()}>
                    <EditableCell
                      value={row.override_currency ?? effectiveCurrency ?? ""}
                      onChange={(v) => onUpdate(row.id, { override_currency: v || null })}
                      placeholder="EUR"
                      className="text-stone w-14"
                    />
                  </td>

                  {/* Cantidad */}
                  <td className="px-4 py-3 font-mono text-xs text-on-dark" onClick={(e) => e.stopPropagation()}>
                    <EditableCell
                      mono
                      value={
                        row.override_quantity !== null
                          ? String(row.override_quantity)
                          : effectiveQty !== null
                          ? String(effectiveQty)
                          : ""
                      }
                      onChange={(v) => {
                        const n = parseFloat(v.replace(",", "."));
                        onUpdate(row.id, { override_quantity: isNaN(n) ? null : n });
                      }}
                      placeholder="0"
                      className="text-on-dark w-24"
                    />
                  </td>

                  {/* Valor capturado */}
                  <td className="px-4 py-3 font-mono text-xs text-on-dark">
                    {row.current_value !== null
                      ? `${fmt(row.current_value)} ${row.current_value_currency ?? ""}`
                      : "—"}
                  </td>

                  {/* Rentabilidad capturada */}
                  <td className="px-4 py-3 font-mono text-xs">
                    {row.return_pct !== null ? (
                      <span className={row.return_pct >= 0 ? "text-emerald-400" : "text-red-400"}>
                        {row.return_pct >= 0 ? "+" : ""}{fmt(row.return_pct)}%
                      </span>
                    ) : (
                      <span className="text-stone">—</span>
                    )}
                  </td>

                  {/* Coste estimado */}
                  <td className="px-4 py-3 font-mono text-xs">
                    {row.override_average_price !== null ? (
                      <span className="text-on-dark">{fmt(row.override_average_price)} €</span>
                    ) : showCostWarning ? (
                      <span className="text-amber-400/80" title="Estimado desde rentabilidad capturada">
                        ~{fmt(row.estimated_cost)} {row.current_value_currency ?? "€"}
                      </span>
                    ) : (
                      <span className="text-stone">—</span>
                    )}
                  </td>

                  {/* Estado */}
                  <td className="px-4 py-3">
                    <ImportStatusBadge
                      status={row.is_manual ? "MANUAL" : row.import_status}
                    />
                  </td>

                  {/* Acciones */}
                  <td className="px-4 py-3" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center gap-2">
                      {!row.is_manual && row.import_status !== "READY" && (
                        <button
                          onClick={() => onMarkManual(row.id)}
                          className="text-[10px] text-stone hover:text-on-dark whitespace-nowrap"
                          title="Importar como manual (sin actualización automática)"
                        >
                          Hacer manual
                        </button>
                      )}
                      <button
                        onClick={() => onDiscard(row.id)}
                        className="text-stone hover:text-red-400 transition-colors"
                        title="Descartar esta posición"
                      >
                        <Trash2 size={13} />
                      </button>
                    </div>
                  </td>
                </tr>

                {/* Expanded detail row */}
                {isExpanded && (
                  <tr key={`${row.id}-detail`} className="bg-white/[.015] border-b border-hairline-dark">
                    <td colSpan={HEADERS.length} className="px-6 py-3">
                      <div className="grid grid-cols-3 gap-4 text-xs text-stone">
                        <div>
                          <p className="text-mute uppercase tracking-wide text-[10px] mb-1">Precio actual</p>
                          <p className="font-mono text-on-dark">
                            {row.price !== null
                              ? `${fmt(row.price)} ${row.price_currency ?? ""}`
                              : "No disponible"}
                          </p>
                        </div>
                        <div>
                          <p className="text-mute uppercase tracking-wide text-[10px] mb-1">Valor en EUR</p>
                          <p className="font-mono text-emerald-400">
                            {row.eur_price !== null ? `${fmt(row.eur_price)} EUR` : "—"}
                          </p>
                        </div>
                        <div>
                          <p className="text-mute uppercase tracking-wide text-[10px] mb-1">Coste medio manual</p>
                          <input
                            className="bg-transparent border-b border-hairline-dark focus:border-primary outline-none font-mono w-32"
                            placeholder="e.g. 100.99"
                            value={row.override_average_price !== null ? String(row.override_average_price) : ""}
                            onChange={(e) => {
                              const n = parseFloat(e.target.value.replace(",", "."));
                              onUpdate(row.id, { override_average_price: isNaN(n) ? null : n });
                            }}
                            onClick={(e) => e.stopPropagation()}
                          />
                        </div>
                        {row.is_cost_estimated && (
                          <div className="col-span-3">
                            <p className="text-amber-400/70 text-[10px] flex items-center gap-1">
                              <AlertCircle size={10} />
                              Coste estimado desde captura — no usar como dato fiscal exacto.
                            </p>
                          </div>
                        )}
                        {row.notes.map((note, i) => (
                          <div key={i} className="col-span-3 text-mute">{note}</div>
                        ))}
                      </div>
                    </td>
                  </tr>
                )}
              </>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
