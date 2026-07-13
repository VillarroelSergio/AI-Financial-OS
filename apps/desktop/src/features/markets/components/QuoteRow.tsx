import { Link } from "react-router-dom";
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
  sparkline?: number[];
}

// MKT-8: mini-gráfica SVG inline (sin recharts por fila). Verde/rojo según primer→último.
function Sparkline({ points }: { points: number[] }) {
  if (points.length < 2) return <div className="h-7" />;
  const w = 64;
  const h = 28;
  const min = Math.min(...points);
  const max = Math.max(...points);
  const span = max - min || 1;
  const step = w / (points.length - 1);
  const d = points
    .map((v, i) => `${i === 0 ? "M" : "L"}${(i * step).toFixed(1)},${(h - ((v - min) / span) * h).toFixed(1)}`)
    .join(" ");
  const up = points[points.length - 1] >= points[0];
  return (
    <svg width={w} height={h} viewBox={`0 0 ${w} ${h}`} className="overflow-visible" aria-hidden="true">
      <path d={d} fill="none" stroke={up ? "#00a87e" : "#e23b4a"} strokeWidth={1.5} strokeLinejoin="round" strokeLinecap="round" />
    </svg>
  );
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

export default function QuoteRow({ quote, sparkline }: Props) {
  const positive = (quote.change_pct ?? 0) >= 0;
  const title = quote.display_name ?? quote.catalog_item_id.replace(/_/g, " ");
  const regionLabel = quote.display_country
    ? (COUNTRY_LABELS[quote.display_country] ?? quote.display_country)
    : null;

  return (
    <Link
      to={`/markets/${encodeURIComponent(quote.catalog_item_id)}`}
      className="grid grid-cols-[1fr_64px_100px_100px] items-center gap-4 px-6 py-3 hover:bg-white/[.03] transition-colors"
    >
      <div className="min-w-0">
        <p className="text-body-sm text-on-dark truncate">{title}</p>
        {regionLabel && (
          <p className="text-caption text-stone">{regionLabel}</p>
        )}
      </div>

      <div className="flex justify-center">
        {sparkline && sparkline.length >= 2 ? <Sparkline points={sparkline} /> : <div className="h-7" />}
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
    </Link>
  );
}
