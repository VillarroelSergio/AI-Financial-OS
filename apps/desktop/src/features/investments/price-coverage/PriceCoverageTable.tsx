import type { CoverageAsset } from "@/lib/types/price-coverage";
import PriceCoverageStatusBadge from "./PriceCoverageStatusBadge";

function formatPrice(price: number | null, currency: string | null): string {
  if (price === null || price === 0) return "—";
  return `${price.toFixed(2)} ${currency ?? ""}`.trim();
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
  "Divisa",
  "Proveedor",
  "Precio",
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
              <td className="px-4 py-3 font-medium text-on-dark whitespace-nowrap">
                {asset.asset_name}
                {asset.notes.length > 0 && (
                  <div className="text-[10px] text-mute mt-0.5">{asset.notes[0]}</div>
                )}
              </td>
              <td className="px-4 py-3 text-stone font-mono text-xs">
                {asset.selected_ticker ?? "—"}
              </td>
              <td className="px-4 py-3 text-stone">{asset.exchange ?? "—"}</td>
              <td className="px-4 py-3 text-stone">{asset.currency ?? "—"}</td>
              <td className="px-4 py-3 text-stone capitalize">{asset.provider ?? "—"}</td>
              <td className="px-4 py-3 text-on-dark font-mono">
                {formatPrice(asset.price, asset.price_currency)}
              </td>
              <td className="px-4 py-3">
                <PriceCoverageStatusBadge status={asset.status} />
              </td>
              <td className="px-4 py-3 text-stone text-xs">{formatDate(asset.last_update)}</td>
              <td className="px-4 py-3">
                {(asset.status === "UNAVAILABLE" ||
                  asset.status === "ERROR" ||
                  asset.status === "PARTIAL") && (
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
