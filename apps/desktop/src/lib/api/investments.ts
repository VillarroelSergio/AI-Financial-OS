import type {
  HoldingEnriched, InvestmentAsset, InvestmentOperation,
  InvestmentSummary, PriceRefreshResult,
} from "@/lib/types";
import { api } from "./client";

export interface AssetCreate {
  name: string;
  ticker?: string | null;
  isin?: string | null;
  asset_type: string;
  currency?: string;
  region?: string | null;
  sector?: string | null;
  price_source?: string;
}

export interface HoldingCreate {
  account_id: string;
  asset_id: string;
  quantity: string;
  average_price: string;
  current_price?: string;
  current_price_currency?: string;
  market_value?: string;
  interest_rate?: string;
  inception_date?: string;
}

export interface HoldingUpdate {
  quantity?: string;
  average_price?: string;
  current_price?: string;
  current_price_currency?: string;
  interest_rate?: string;
  inception_date?: string;
}

export interface OperationCreate {
  account_id: string;
  asset_id: string;
  date: string;
  operation_type: string;
  quantity?: string;
  price?: string;
  amount: string;
  currency?: string;
  fees?: string;
}

export interface AssetSearchCandidate {
  ticker: string;
  name: string;
  exchange: string;
  currency: string;
  asset_type: string;
  requires_confirmation: boolean;
  confirmation_note: string;
}

export const searchAssetCandidates = (query: string) =>
  api.get<AssetSearchCandidate[]>(`/api/investments/assets/search?q=${encodeURIComponent(query)}`);

export const getAssets = () =>
  api.get<InvestmentAsset[]>("/api/investments/assets");

export const createAsset = (data: AssetCreate) =>
  api.post<InvestmentAsset>("/api/investments/assets", data);

export const updateAsset = (id: string, data: Partial<AssetCreate>) =>
  api.patch<InvestmentAsset>(`/api/investments/assets/${id}`, data);

export const deleteAsset = (id: string) =>
  api.delete<void>(`/api/investments/assets/${id}`);

export const getHoldings = (accountId?: string) =>
  api.get<HoldingEnriched[]>(
    `/api/investments/holdings${accountId ? `?account_id=${accountId}` : ""}`
  );

export const createHolding = (data: HoldingCreate) =>
  api.post<HoldingEnriched>("/api/investments/holdings", data);

export const updateHolding = (id: string, data: HoldingUpdate) =>
  api.patch<HoldingEnriched>(`/api/investments/holdings/${id}`, data);

export const deleteHolding = (id: string) =>
  api.delete<void>(`/api/investments/holdings/${id}`);

export const mergeHoldings = (sourceId: string, targetId: string) =>
  api.post<HoldingEnriched>("/api/investments/holdings/merge", { source_id: sourceId, target_id: targetId });

export interface HoldingPerformancePoint {
  date: string;
  price: number;
}

export interface HoldingPerformance {
  holding_id: string;
  name: string;
  ticker: string;
  currency: string;
  entry_date: string;
  entry_price: number;
  entry_source: "operation" | "holding" | "history" | "fund_snapshot";
  current_price: number;
  change_pct: number | null;
  series: HoldingPerformancePoint[];
}

export const getHoldingPerformance = (holdingId: string) =>
  api.get<HoldingPerformance>(`/api/investments/holdings/${holdingId}/performance`);

export interface HoldingValueHistoryEntry {
  id: string;
  holding_id: string;
  price: string;
  currency: string;
  source: string;
  recorded_at: string;
}

export const getHoldingHistory = (holdingId: string) =>
  api.get<HoldingValueHistoryEntry[]>(`/api/investments/holdings/${holdingId}/history`);

export const addHoldingHistory = (holdingId: string, data: { price: string; currency?: string; recorded_at?: string }) =>
  api.post<HoldingValueHistoryEntry>(`/api/investments/holdings/${holdingId}/history`, data);

export const updateHoldingHistory = (holdingId: string, entryId: string, data: { price?: string; recorded_at?: string }) =>
  api.patch<HoldingValueHistoryEntry>(`/api/investments/holdings/${holdingId}/history/${entryId}`, data);

export const deleteHoldingHistory = (holdingId: string, entryId: string) =>
  api.delete<void>(`/api/investments/holdings/${holdingId}/history/${entryId}`);

// ── Fondos (INV-3, spec §3) ─────────────────────────────────────────────────

export interface FundValuationSnapshot {
  id: string;
  holding_id: string;
  date: string;
  market_value: string;
  contributed_total: string | null;
  units: string | null;
  nav: string | null;
  currency: string;
  source: string;
  note: string | null;
  created_at: string;
}

export const createFund = (data: {
  name: string; account_id: string; contributed: string; value: string; date: string;
  units?: string | null; nav?: string | null; currency?: string;
}) => api.post<HoldingEnriched>("/api/investments/funds", data);

export const getFundSnapshots = (holdingId: string) =>
  api.get<FundValuationSnapshot[]>(`/api/investments/funds/${holdingId}/snapshots`);

export const addFundSnapshot = (
  holdingId: string,
  data: { date: string; market_value: string; contributed_total?: string; units?: string | null; nav?: string | null; currency?: string; note?: string },
) =>
  api.post<FundValuationSnapshot>(`/api/investments/funds/${holdingId}/snapshots`, data);

export const updateFundSnapshot = (
  snapshotId: string,
  data: { date?: string; market_value?: string; contributed_total?: string; note?: string },
) =>
  api.put<FundValuationSnapshot>(`/api/investments/funds/snapshots/${snapshotId}`, data);

export const deleteFundSnapshot = (snapshotId: string) =>
  api.delete<void>(`/api/investments/funds/snapshots/${snapshotId}`);

// ── Cuentas remuneradas (INV-4, spec §3) ────────────────────────────────────

export interface SavingsSchedulePoint {
  month: string;
  balance_start: string;
  annual_rate: string;
  interest: string;
  contributions: string;
  balance_end: string;
}

export interface SavingsProjection {
  points: SavingsSchedulePoint[];
  total_interest: string;
  total_contributions: string;
  current_balance: string;
  current_rate: string | null;
  estimated: boolean;
}

export const createSavings = (data: {
  account_id?: string; new_account_name?: string; institution?: string;
  opened_at: string; balance: string; rate_source?: string; fixed_rate?: string; spread_bps?: number;
}) => api.post<unknown>("/api/investments/savings", data);

export const getSavingsProjection = (accountId: string, asOf?: string) =>
  api.get<SavingsProjection>(
    `/api/investments/savings/${accountId}/projection${asOf ? `?as_of=${asOf}` : ""}`,
  );

export interface SavingsConfig {
  id: string;
  account_id: string;
  opened_at: string | null;
  rate_source: string;
  fixed_rate: string | null;
  spread_bps: number;
  compounding: string;
}

export const getSavingsConfig = (accountId: string) =>
  api.get<SavingsConfig>(`/api/investments/savings/${accountId}`);

export const updateSavings = (
  accountId: string,
  data: { opened_at?: string; rate_source?: string; fixed_rate?: string | null; spread_bps?: number },
) => api.put<SavingsConfig>(`/api/investments/savings/${accountId}`, data);

export const deleteSavings = (accountId: string) =>
  api.delete<void>(`/api/investments/savings/${accountId}`);

export const getOperations = (accountId?: string) =>
  api.get<InvestmentOperation[]>(
    `/api/investments/operations${accountId ? `?account_id=${accountId}` : ""}`
  );

export const createOperation = (data: OperationCreate) =>
  api.post<InvestmentOperation>("/api/investments/operations", data);

export const getSummary = () =>
  api.get<InvestmentSummary>("/api/investments/summary");

export interface PortfolioEvolutionPoint {
  month: string;
  value: number;
}

export const getPortfolioEvolution = () =>
  api.get<{ series: PortfolioEvolutionPoint[]; currency: string }>(
    "/api/investments/holdings/portfolio-evolution",
  );

export const refreshPrices = () =>
  api.post<PriceRefreshResult>("/api/investments/prices/refresh", {});

// ── Reconciliation ────────────────────────────────────────────────────────────

export interface ReconciliationHolding {
  holding_id: string;
  display_name: string;
  ticker: string | null;
  quality_state: "confirmed" | "estimated" | "manual" | "no_price" | "fx_pending" | "requires_review";
  value_eur: number;
  weight_pct: number;
  unrealized_pnl: number;
  unrealized_pnl_pct: number;
  currency: string;
  requires_fx: boolean;
  broker: string;
  sector: string | null;
  asset_type: string;
}

export interface WeightItem {
  key: string;
  weight_pct: number;
}

export interface ConcentrationAlert {
  type: "asset" | "currency";
  key: string;
  weight_pct: number;
  threshold_pct: number;
}

export interface ReconciliationReport {
  generated_at: string;
  portfolio_value_eur: number;
  completeness: {
    confirmed_pct: number;
    estimated_pct: number;
    manual_pct: number;
    no_price_pct: number;
  };
  holdings: ReconciliationHolding[];
  weights_by: {
    currency: WeightItem[];
    sector: WeightItem[];
    broker: WeightItem[];
    asset_type: WeightItem[];
    region: WeightItem[];
  };
  concentration_alerts: ConcentrationAlert[];
}

export const fetchReconciliation = (): Promise<ReconciliationReport> =>
  api.get<ReconciliationReport>("/api/investments/reconciliation");
