import { useCallback, useEffect, useState } from "react";
import { getQuotes } from "@/lib/api/markets";
import type { MarketQuote } from "@/lib/types";

export function useMarkets(): {
  quotes: MarketQuote[];
  loading: boolean;
  error: string | null;
} {
  const [quotes, setQuotes] = useState<MarketQuote[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await getQuotes();
      setQuotes(data);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar datos de mercado");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return { quotes, loading, error };
}
