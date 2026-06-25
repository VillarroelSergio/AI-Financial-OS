// apps/desktop/src/lib/hooks/useMarkets.ts
import { useCallback, useEffect, useState } from "react";
import { getQuotes, refreshQuotes } from "@/lib/api/markets";
import type { MarketQuote } from "@/lib/types";

export function useMarkets(): {
  quotes: MarketQuote[];
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  secondsSinceUpdate: number;
  refreshing: boolean;
  refresh: () => Promise<void>;
} {
  const [quotes, setQuotes] = useState<MarketQuote[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [secondsSinceUpdate, setSecondsSinceUpdate] = useState(0);
  const [refreshing, setRefreshing] = useState(false);

  // Load all quotes from cache only (no external API calls).
  // Category filtering happens client-side so tab switches need no refetch.
  const load = useCallback(async () => {
    try {
      const data = await getQuotes();
      setQuotes(data);
      setLastUpdated(new Date());
      setSecondsSinceUpdate(0);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar datos de mercado");
    } finally {
      setLoading(false);
    }
  }, []);

  // Initial cache read on mount — does NOT call external APIs.
  useEffect(() => { load(); }, [load]);

  // This timer only updates the age label; it never performs network requests.
  useEffect(() => {
    const id = window.setInterval(() => {
      if (lastUpdated) {
        setSecondsSinceUpdate(Math.floor((Date.now() - lastUpdated.getTime()) / 1000));
      }
    }, 1000);
    return () => window.clearInterval(id);
  }, [lastUpdated]);

  // Refresh calls external APIs — only triggered by the user pressing the button.
  const refresh = useCallback(async () => {
    if (refreshing) return;
    setRefreshing(true);
    try {
      const data = await refreshQuotes();
      setQuotes(data);
      setLastUpdated(new Date());
      setSecondsSinceUpdate(0);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al actualizar datos de mercado");
    } finally {
      setRefreshing(false);
      setLoading(false);
    }
  }, [refreshing]);

  return { quotes, loading, error, lastUpdated, secondsSinceUpdate, refreshing, refresh };
}
