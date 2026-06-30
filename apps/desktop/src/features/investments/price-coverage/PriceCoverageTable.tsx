import type { CoverageAsset } from "@/lib/types/price-coverage";
import PriceCoverageStatusBadge from "./PriceCoverageStatusBadge";

function formatPrice(price: number | null, currency: string | null): string {
  if (price === null || price === 0) return "—";
  return `${price.toFixed(2)} ${currency ?? ""}`.trim();
}

function formatEurPrice(eur: number | null): string {
  if (eur === null) return "—";
  return `${eur.toFixed(2)} EUR`;
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

const HEADERS = [
  "Activo",
  "Ticker",
  "Mercado",
  "Precio original",
  "Divisa",
  "Valor en EUR",
  "Estado",
  "Última act.",
  "",
];

interface Props {
  assets: CoverageAsset[];
  onRetry: (assetName: string) => void;
}

export default function PriceCoverageTable({ assets, onRetry }: Props) {
  if (assets.length === 0) {
    return (
      <p className="text-mute text-sm py-8 text-center">
        Pulsa "Auditar" para comprobar la cobertura de precios.
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
          {assets.map((asset) => (
            <tr
              key={asset.asset_name}
              className="border-b border-hairline-dark last:border-0 hover:bg-white/[.02] transition-colors"
            >
              {/* Activo */}
              <td className="px-4 py-3 font-medium text-on-dark whitespace-nowrap">
                {asset.asset_name}
                {asset.notes.length > 0 && (
                  <div className="text-[10px] text-mute mt-0.5 max-w-[200px] leading-tight">
                    {asset.notes[0]}
                  </div>
                )}
              </td>

              {/* Ticker */}
              <td className="px-4 py-3 text-stone font-mono text-xs">
                {asset.selected_ticker ?? "—"}
              </td>

              {/* Mercado */}
              <td className="px-4 py-3 text-stone">{asset.exchange ?? "—"}</td>

              {/* Precio original */}
              <td className="px-4 py-3 text-on-dark font-mono">
                {formatPrice(asset.price, null)}
              </td>

              {/* Divisa */}
              <td className="px-4 py-3">
                {asset.price_currency ? (
                  <span className={`font-mono text-xs ${asset.requires_fx_conversion ? "text-amber-400" : "text-stone"}`}>
                    {asset.price_currency}
                  </span>
                ) : (
                  <span className="text-stone">—</span>
                )}
              </td>

              {/* Valor en EUR */}
              <td className="px-4 py-3 font-mono">
                {asset.eur_price !== null ? (
                  <span className="text-emerald-400">{formatEurPrice(asset.eur_price)}</span>
                ) : asset.status === "FX_PENDING" ? (
                  <span className="text-amber-400/60 text-xs">FX no disponible</span>
                ) : (
                  <span className="text-stone">—</span>
                )}
              </td>

              {/* Estado */}
              <td className="px-4 py-3">
                <PriceCoverageStatusBadge status={asset.status} />
              </td>

              {/* Última actualización */}
              <td className="px-4 py-3 text-stone text-xs">{formatDate(asset.last_update)}</td>

              {/* Acciones */}
              <td className="px-4 py-3">
                {(asset.status === "UNAVAILABLE" || asset.status === "ERROR") && (
                  <button
                    onClick={() => onRetry(asset.asset_name)}
                    className="text-xs text-primary-bright hover:underline"
                  >
                    Reintentar
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
