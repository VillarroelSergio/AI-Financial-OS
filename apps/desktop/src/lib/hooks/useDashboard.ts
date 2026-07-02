import { useEffect, useState } from "react";
import {
  fetchCategorySpendingDetail,
  fetchOverview,
  fetchSpending,
  fetchSpendingYears,
  type CategorySpendingDetail,
  type SpendingData,
} from "@/lib/api/dashboard";
import { useAsyncData } from "@/lib/hooks/useAsyncData";
import type { DashboardOverview } from "@/lib/types";

export function useOverview() {
  const { data, loading } = useAsyncData<DashboardOverview>(fetchOverview);
  return { data, loading };
}

export function useSpending(period: { mode: "month" | "year"; month: string; year: number }) {
  const [data, setData] = useState<SpendingData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchSpending(period.mode === "year" ? { year: period.year } : { month: period.month })
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [period.mode, period.month, period.year]);

  return { data, loading };
}

export function useSpendingYears() {
  const { data } = useAsyncData(fetchSpendingYears);
  return data?.years ?? [];
}

export function useCategorySpendingDetail(
  categoryId: string | null | undefined,
  period: { mode: "month" | "year"; month: string; year: number },
) {
  const [data, setData] = useState<CategorySpendingDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (categoryId === undefined) return;
    setLoading(true);
    setError(null);
    fetchCategorySpendingDetail(
      categoryId,
      period.mode === "year" ? { year: period.year } : { month: period.month },
    )
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : "No se pudieron cargar los movimientos"))
      .finally(() => setLoading(false));
  }, [categoryId, period.mode, period.month, period.year]);

  return { data, loading, error };
}
