import { formatCurrency } from "@/lib/formatters/currency";
import type { HoldingEnriched } from "@/lib/types";

interface Bucket {
  key: string;
  label: string;
  types: string[];
  badge: string;
  badgeClass: string;
}

// Desglose por tipo con badge de calidad alineado a Reconciliation (INV-6):
// mercado = precio de mercado, fondos = valor manual, ahorro = cálculo determinista.
const BUCKETS: Bucket[] = [
  { key: "mercado", label: "Acciones y ETF", types: ["stock", "etf", "crypto", "bond"], badge: "Mercado", badgeClass: "bg-accent-teal/15 text-accent-teal" },
  { key: "fondos", label: "Fondos", types: ["fund"], badge: "Manual", badgeClass: "bg-[var(--bg-interactive)] text-stone" },
  { key: "ahorro", label: "Ahorro", types: ["savings_account", "cash"], badge: "Calculado", badgeClass: "bg-sky-500/15 text-sky-400" },
];

export default function PortfolioByTypeCards({
  holdings,
  fundReportedReturnPercent,
}: {
  holdings: HoldingEnriched[];
  fundReportedReturnPercent: number | null;
}) {
  const cards = BUCKETS.map((b) => {
    const items = holdings.filter((h) => b.types.includes(h.asset.asset_type));
    const value = items.reduce((s, h) => s + Number(h.market_value ?? 0), 0);
    const invested = items.reduce((s, h) => s + Number(h.invested_amount ?? 0), 0);
    const pending = items.filter((h) => h.market_value === null).length;
    const simpleReturnPct = invested > 0 ? ((value - invested) / invested) * 100 : null;
    const usesReportedReturn = b.key === "fondos" && fundReportedReturnPercent !== null;
    const returnPct = usesReportedReturn ? fundReportedReturnPercent : simpleReturnPct;
    return { ...b, count: items.length, value, returnPct, pending, usesReportedReturn };
  }).filter((c) => c.count > 0);

  if (cards.length === 0) return null;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-xl">
      {cards.map((c) => {
        const positive = c.returnPct !== null && c.returnPct >= 0;
        return (
          <div key={c.key} className="bg-surface-card border border-hairline-dark rounded-md p-lg">
            <div className="flex items-center justify-between gap-sm mb-sm">
              <span className="text-caption text-stone">{c.label}</span>
              <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-medium ${c.badgeClass}`}>{c.badge}</span>
            </div>
            <p className="text-heading-sm text-on-dark">{formatCurrency(c.value.toFixed(2))}</p>
            <div className="flex items-center gap-sm mt-xs">
              {c.returnPct !== null && (
                <span className={`text-caption ${positive ? "text-accent-teal" : "text-accent-danger"}`}>
                  {positive ? "+" : ""}{c.returnPct.toFixed(2)}%
                  <span className="ml-1 text-mute">{c.usesReportedReturn ? "reportada" : "s/aportado"}</span>
                </span>
              )}
              <span className="text-caption text-mute">{c.count} posición{c.count === 1 ? "" : "es"}</span>
            </div>
            {c.pending > 0 && (
              <p className="text-[11px] text-accent-warning mt-xs">{c.pending} sin valorar</p>
            )}
          </div>
        );
      })}
    </div>
  );
}
