import { useEffect, useState } from "react";
import { fetchOverview, fetchSpending, type SpendingData } from "@/lib/api/dashboard";
import type { DashboardOverview } from "@/lib/types";

export function useOverview() {
  const [data, setData] = useState<DashboardOverview | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchOverview()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return { data, loading };
}

export function useSpending(month: string) {
  const [data, setData] = useState<SpendingData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchSpending(month)
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [month]);

  return { data, loading };
}
