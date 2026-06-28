import { useEffect, useState } from "react";
import { getMonthlyReview } from "../api/insightsApi";
import type { MonthlyReview } from "../types/insights.types";

export function useMonthlyReview(period?: string) {
  const [data, setData] = useState<MonthlyReview | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    getMonthlyReview(period)
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "Error al cargar resumen mensual"))
      .finally(() => setLoading(false));
  }, [period]);

  return { data, loading, error };
}
