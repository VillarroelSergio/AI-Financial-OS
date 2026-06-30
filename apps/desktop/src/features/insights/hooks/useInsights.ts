import { useCallback, useEffect, useState } from "react";
import { getInsights } from "../api/insightsApi";
import type { InsightsSummary, InsightsParams } from "../types/insights.types";

export function useInsights(params: InsightsParams = {}, deps: unknown[] = []) {
  const [data, setData] = useState<InsightsSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    getInsights(params)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar insights"))
      .finally(() => setLoading(false));
  }, deps); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => { load(); }, [load]);

  return { data, loading, error, refresh: load };
}
