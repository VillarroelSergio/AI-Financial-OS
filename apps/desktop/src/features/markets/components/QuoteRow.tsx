// apps/desktop/src/features/markets/components/QuoteRow.tsx
import { useEffect, useRef, useState } from "react";
import type { MarketQuote } from "@/lib/types";
import MiniSparkline from "./MiniSparkline";

interface Props {
  quote: MarketQuote;
}

function formatPrice(price: number): string {
  const decimals = price < 10 ? 4 : 2;
  return price.toLocaleString("es-ES", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export default function QuoteRow({ quote }: Props) {
  const prevPrice = useRef<number | null>(null);
  const [flashClass, setFlashClass] = useState("");

  useEffect(() => {
    if (
      prevPrice.current !== null &&
      quote.price !== null &&
      quote.price !== prevPrice.current
    ) {
      const cls = quote.price > prevPrice.current ? "flash-up" : "flash-down";
      setFlashClass(cls);
      const t = setTimeout(() => setFlashClass(""), 400);
      return () => clearTimeout(t);
    }
    prevPrice.current = quote.price ?? null;
  }, [quote.price]);

  const positive = (quote.change_pct ?? 0) >= 0;

  return (
    <div className={`flex items-center gap-4 px-6 py-3 ${flashClass}`}>
      <div className="flex-1 min-w-0">
        <p className="text-body-sm text-on-dark truncate">{quote.name}</p>
        <p className="text-caption text-stone">{quote.symbol}</p>
      </div>

      <MiniSparkline sparkline={quote.sparkline} changePct={quote.change_pct} />

      <div className="text-right min-w-[100px]">
        {quote.price !== null ? (
          <p className="text-body-sm font-semibold text-on-dark tabular-nums">
            {formatPrice(quote.price)}
          </p>
        ) : (
          <p className="text-body-sm text-stone">—</p>
        )}
        <p className="text-caption text-stone">{quote.currency}</p>
      </div>

      <div className="min-w-[72px] text-right">
        {quote.change_pct !== null ? (
          <span
            className={`inline-flex items-center text-caption rounded-full px-[10px] py-[3px] ${
              positive
                ? "bg-accent-teal/15 text-accent-teal"
                : "bg-accent-danger/15 text-accent-danger"
            }`}
          >
            {positive ? "▲" : "▼"} {Math.abs(quote.change_pct).toFixed(2)}%
          </span>
        ) : (
          <span className="text-caption text-stone">—</span>
        )}
      </div>
    </div>
  );
}
