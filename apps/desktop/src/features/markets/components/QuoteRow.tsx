import type { QuoteMI } from "@/lib/types/market-intelligence";

const COUNTRY_LABELS: Record<string, string> = {
  US: "🇺🇸 EE.UU.",
  ES: "🇪🇸 España",
  DE: "🇩🇪 Alemania",
  FR: "🇫🇷 Francia",
  GB: "🇬🇧 Reino Unido",
  JP: "🇯🇵 Japón",
  EA: "🇪🇺 Eurozona",
  GLOBAL: "🌐 Global",
};

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

function DataStatusBadge({ status }: { status: QuoteMI["data_status"] }) {
  if (!status || status === "ok") return null;

  const config: Record<
    Exclude<QuoteMI["data_status"], "ok" | undefined>,
    { label: string; className: string }
  > = {
    limited: { label: "Limitado", className: "bg-amber-400/10 text-amber-400" },
    unavailable: { label: "Sin dato", className: "bg-white/5 text-stone" },
    requires_review: { label: "Revisar", className: "bg-accent-danger/10 text-accent-danger" },
  };

  const { label, className } = config[status];
  return (
    <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${className}`}>
      {label}
    </span>
  );
}

export default function QuoteRow({ quote }: Props) {
  const positive = (quote.change_pct ?? 0) >= 0;
  const title = quote.display_name ?? quote.catalog_item_id.replace(/_/g, " ");
  const regionLabel = quote.display_country
    ? (COUNTRY_LABELS[quote.display_country] ?? quote.display_country)
    : null;

  return (
    <div className="grid grid-cols-[1fr_100px_100px] items-center gap-4 px-6 py-3">
      <div className="min-w-0">
        <p className="text-body-sm text-on-dark truncate">{title}</p>
        {regionLabel && (
          <p className="text-caption text-stone">{regionLabel}</p>
        )}
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
              positive
                ? "bg-accent-teal/15 text-accent-teal"
                : "bg-accent-danger/15 text-accent-danger",
            ].join(" ")}
          >
            <span aria-hidden="true">{positive ? "▲" : "▼"}</span>
            {Math.abs(quote.change_pct).toFixed(2)}%
          </span>
        ) : (
          <span className="text-caption text-stone">—</span>
        )}
        <DataStatusBadge status={quote.data_status} />
      </div>
    </div>
  );
}
