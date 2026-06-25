// apps/desktop/src/lib/hooks/useMarkets.ts
import { useCallback, useEffect, useRef, useState } from "react";
import { getQuotes } from "@/lib/api/markets";
import type { MarketQuote } from "@/lib/types";

function useInterval(callback: () => void, delay: number | null) {
  const savedCallback = useRef(callback);
  useEffect(() => { savedCallback.current = callback; }, [callback]);
  useEffect(() => {
    if (delay === null) return;
    const id = setInterval(() => savedCallback.current(), delay);
    return () => clearInterval(id);
  }, [delay]);
}

export function useMarkets(category?: string): {
  quotes: MarketQuote[];
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  secondsSinceUpdate: number;
} {
  const [quotes, setQuotes] = useState<MarketQuote[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [secondsSinceUpdate, setSecondsSinceUpdate] = useState(0);
  const [paused, setPaused] = useState(false);

  const load = useCallback(async () => {
    if (paused) return;
    try {
      const data = await getQuotes(category);
      setQuotes(data);
      setLastUpdated(new Date());
      setSecondsSinceUpdate(0);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar datos de mercado");
    } finally {
      setLoading(false);
    }
  }, [category, paused]);

  // Initial load
  useEffect(() => { load(); }, [load]);

  // Polling every 5s
  useInterval(load, 5000);

  // Tick secondsSinceUpdate every second
  useInterval(() => {
    if (lastUpdated) {
      setSecondsSinceUpdate(Math.floor((Date.now() - lastUpdated.getTime()) / 1000));
    }
  }, 1000);

  // Pause when tab is hidden
  useEffect(() => {
    const handleVisibility = () => setPaused(document.hidden);
    document.addEventListener("visibilitychange", handleVisibility);
    return () => document.removeEventListener("visibilitychange", handleVisibility);
  }, []);

  return { quotes, loading, error, lastUpdated, secondsSinceUpdate };
}
