import { useCallback, useEffect, useState } from "react";
import {
  createHolding, deleteHolding, fetchReconciliation, getHoldings, getSummary,
  refreshPrices, updateHolding,
  type HoldingCreate, type HoldingUpdate, type ReconciliationReport,
} from "@/lib/api/investments";
import { useAsyncData } from "@/lib/hooks/useAsyncData";
import type { HoldingEnriched, InvestmentSummary, PriceRefreshResult } from "@/lib/types";

export function useInvestmentSummary() {
  const { data: summary, loading, error, reload } = useAsyncData<InvestmentSummary>(getSummary);
  return { summary, loading, error, refresh: reload };
}

export function useHoldings(accountId?: string) {
  const [holdings, setHoldings] = useState<HoldingEnriched[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setHoldings(await getHoldings(accountId));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar posiciones");
    } finally {
      setLoading(false);
    }
  }, [accountId]);

  useEffect(() => { load(); }, [load]);

  const add = async (data: HoldingCreate) => {
    const holding = await createHolding(data);
    setHoldings(prev => [...prev, holding]);
    return holding;
  };

  const update = async (id: string, data: HoldingUpdate) => {
    const holding = await updateHolding(id, data);
    setHoldings(prev => prev.map(h => (h.id === id ? holding : h)));
    return holding;
  };

  const remove = async (id: string) => {
    await deleteHolding(id);
    setHoldings(prev => prev.filter(h => h.id !== id));
  };

  return { holdings, loading, error, refresh: load, add, update, remove };
}

export function useRefreshPrices(onRefresh: () => void) {
  const [refreshing, setRefreshing] = useState(false);
  const [result, setResult] = useState<PriceRefreshResult | null>(null);
  const [needsManualNav, setNeedsManualNav] = useState<string[]>([]);

  const refresh = async () => {
    setRefreshing(true);
    try {
      const result: PriceRefreshResult = await refreshPrices();
      setResult(result);
      setNeedsManualNav(result.manual_required.map((item) => item.holding_id));
      onRefresh();
    } catch {
      // keep previous prices on failure
    } finally {
      setRefreshing(false);
    }
  };

  const clearNeedsManualNav = () => setNeedsManualNav([]);
  const clearResult = () => setResult(null);

  return { refresh, refreshing, result, needsManualNav, clearNeedsManualNav, clearResult };
}

export function useReconciliation() {
  const { data, loading, error, reload } = useAsyncData<ReconciliationReport>(fetchReconciliation);
  return { data, loading, error, refresh: reload };
}
