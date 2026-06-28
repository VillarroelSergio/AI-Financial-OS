// apps/desktop/src/features/markets/components/QuoteRow.tsx
import type { QuoteMI } from "@/lib/types/market-intelligence";

interface Props {
  quote: QuoteMI;
}

function formatPrice(price: number): string {
  const decimals = price < 10 ? 4 : 2;
  return price.toLocaleString("es-ES", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export default function QuoteRow({ quote }: Props) {
  const positive = (quote.change_pct ?? 0) >= 0;
  const qualityColor =
    quote.quality_score >= 0.8
      ? "bg-accent-success/15 text-accent-success"
      : quote.quality_score >= 0.5
      ? "bg-amber-400/15 text-amber-400"
      : "bg-accent-danger/15 text-accent-danger";

  return (
    <div className="grid grid-cols-[1fr_100px_100px] items-center gap-4 px-6 py-3">
      <div className="min-w-0">
        <p className="text-body-sm text-on-dark truncate">
          {quote.symbol ?? quote.catalog_item_id}
        </p>
        <p className="text-caption text-stone">{quote.catalog_item_id.replace(/_/g, " ")}</p>
      </div>

      <div className="text-right">
        {quote.price != null ? (
          <>
            <p className="text-body-sm font-semibold text-on-dark tabular-nums">
              {formatPrice(quote.price)}
            </p>
            <p className="text-caption text-stone">{quote.currency ?? "—"}</p>
          </>
        ) : (
          <p className="text-body-sm text-stone">—</p>
        )}
      </div>

      <div className="text-right flex flex-col items-end gap-1">
        {quote.change_pct != null ? (
          <span
            className={[
              "inline-flex items-center gap-1 text-caption rounded-full px-2.5 py-[3px] font-medium",
              positive ? "bg-accent-teal/15 text-accent-teal" : "bg-accent-danger/15 text-accent-danger",
            ].join(" ")}
          >
            <span aria-hidden="true">{positive ? "▲" : "▼"}</span>
            {Math.abs(quote.change_pct).toFixed(2)}%
          </span>
        ) : (
          <span className="text-caption text-stone">—</span>
        )}
        <span className={`text-[10px] rounded px-1.5 py-px ${qualityColor}`}>
          {(quote.quality_score * 100).toFixed(0)}%
        </span>
      </div>
    </div>
  );
}
