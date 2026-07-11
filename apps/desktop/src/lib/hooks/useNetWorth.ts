import { useCallback } from "react";
import {
  createSnapshot,
  fetchBalanceSheet,
  fetchReadiness,
  fetchSnapshots,
  type BalanceSheet,
  type NetWorthSnapshot,
  type Readiness,
} from "@/lib/api/net-worth";
import { useAsyncData } from "@/lib/hooks/useAsyncData";

export function useBalanceSheet(month?: string) {
  const fetcher = useCallback(() => fetchBalanceSheet(month), [month]);
  return useAsyncData<BalanceSheet>(fetcher);
}

export function useSnapshots() {
  return useAsyncData<NetWorthSnapshot[]>(fetchSnapshots);
}

export function useReadiness(month?: string) {
  const fetcher = useCallback(() => fetchReadiness(month), [month]);
  return useAsyncData<Readiness>(fetcher);
}

export { createSnapshot };
