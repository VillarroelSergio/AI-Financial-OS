// apps/desktop/src/features/markets/components/QuoteRow.tsx
import { useEffect, useRef, useState } from "react";
import type { MarketQuote } from "@/lib/types";
import MiniSparkline from "./MiniSparkline";

interface Props {
  quote: MarketQuote;
  isSelected?: boolean;
  onSelect?: (symbol: string) => void;
}

function formatPrice(price: number): string {
  const decimals = price < 10 ? 4 : 2;
  return price.toLocaleString("es-ES", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

function deriveChangeAbs(price: number | null, changePct: number | null): number | null {
  if (price === null || changePct === null) return null;
  // previous = price / (1 + changePct/100), changeAbs = price - previous
  const previous = price / (1 + changePct / 100);
  return price - previous;
}

function formatChangeAbs(value: number): string {
  const abs = Math.abs(value);
  const decimals = abs < 10 ? 4 : 2;
  return value.toLocaleString("es-ES", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
    signDisplay: "exceptZero",
  });
}

export default function QuoteRow({ quote, isSelected = false, onSelect }: Props) {
  const prevPrice = useRef<number | null>(null);
  const [flashClass, setFlashClass] = useState("");

  useEffect(() => {
    let t: ReturnType<typeof setTimeout> | undefined;
    if (
      prevPrice.current !== null &&
      quote.price !== null &&
      quote.price !== prevPrice.current
    ) {
      const cls = quote.price > prevPrice.current ? "flash-up" : "flash-down";
      setFlashClass(cls);
      t = setTimeout(() => setFlashClass(""), 300);
    }
    prevPrice.current = quote.price ?? null;
    return () => clearTimeout(t);
  }, [quote.price]);

  const positive = (quote.change_pct ?? 0) >= 0;
  const changeAbs = deriveChangeAbs(quote.price, quote.change_pct);
  const isInteractive = Boolean(onSelect);

  return (
    <div
      role={isInteractive ? "button" : undefined}
      tabIndex={isInteractive ? 0 : undefined}
      aria-pressed={isInteractive ? isSelected : undefined}
      aria-label={
        isInteractive
          ? `${quote.name} (${quote.symbol}), precio ${quote.price !== null ? formatPrice(quote.price) : "no disponible"}`
          : undefined
      }
      onClick={isInteractive ? () => onSelect!(quote.symbol) : undefined}
      onKeyDown={
        isInteractive
          ? (e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onSelect!(quote.symbol);
              }
            }
          : undefined
      }
      className={[
        "grid grid-cols-[1fr_80px_120px_100px] items-center gap-4 px-6 py-3 transition-colors duration-150",
        flashClass,
        isInteractive
          ? "cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-primary"
          : "",
        isSelected
          ? "bg-surface-card"
          : isInteractive
          ? "hover:bg-surface-card/60"
          : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {/* Nombre + ticker */}
      <div className="min-w-0">
        <p className="text-body-sm text-on-dark truncate">{quote.name}</p>
        <p className="text-caption text-stone">{quote.symbol}</p>
      </div>

      {/* Sparkline */}
      <div className="flex justify-center">
        <MiniSparkline sparkline={quote.sparkline} changePct={quote.change_pct} />
      </div>

      {/* Precio */}
      <div className="text-right">
        {quote.price !== null ? (
          <p className="text-body-sm font-semibold text-on-dark tabular-nums">
            {formatPrice(quote.price)}
          </p>
        ) : (
          <p className="text-body-sm text-stone">—</p>
        )}
        <p className="text-caption text-stone">{quote.currency}</p>
      </div>

      {/* Cambio % + pts */}
      <div className="text-right flex flex-col items-end gap-0.5">
        {quote.change_pct !== null ? (
          <>
            <span
              aria-label={`${positive ? "subida" : "bajada"} ${Math.abs(quote.change_pct).toFixed(2)} por ciento`}
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
            {changeAbs !== null && (
              <span className="text-caption text-stone tabular-nums">
                {formatChangeAbs(changeAbs)} pts
              </span>
            )}
          </>
        ) : (
          <span className="text-caption text-stone">—</span>
        )}
      </div>
    </div>
  );
}
