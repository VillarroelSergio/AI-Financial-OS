import { api } from "./client";
import { buildQueryString } from "./queryParams";

export interface BalanceLine {
  key: string;
  label: string;
  amount: string;
}

export interface BalanceSheet {
  month: string;
  assets: BalanceLine[];
  liabilities: BalanceLine[];
  total_assets: string;
  total_liabilities: string;
  net_worth: string;
  portfolio_cost: string;
  portfolio_gain: string;
  net_worth_change: string | null;
  currency: string;
}

export type ReadinessStatus = "ok" | "stale" | "missing";

export interface ReadinessItem {
  key: string;
  label: string;
  status: ReadinessStatus;
  detail: string;
  cta_route: string | null;
}

export interface Readiness {
  month: string;
  items: ReadinessItem[];
  ready: boolean;
  snapshot_exists: boolean;
  snapshot_state: "complete" | "partial" | null;
}

export interface NetWorthSnapshot {
  id: string;
  month: string;
  snapshot_date: string;
  total_assets: string;
  total_liabilities: string;
  net_worth: string;
  data_state: string;
  missing_items: string[];
  currency: string;
  created_at: string;
}

export const fetchBalanceSheet = (month?: string) =>
  api.get<BalanceSheet>(`/api/net-worth/balance-sheet${buildQueryString({ month })}`);

export const fetchSnapshots = (from?: string, to?: string) =>
  api.get<NetWorthSnapshot[]>(`/api/net-worth/snapshots${buildQueryString({ from, to })}`);

export const fetchReadiness = (month?: string) =>
  api.get<Readiness>(`/api/net-worth/snapshot-readiness${buildQueryString({ month })}`);

export const createSnapshot = (month: string, force_partial: boolean) =>
  api.post<NetWorthSnapshot>("/api/net-worth/snapshots", { month, force_partial });
