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

export const getOperations = (accountId?: string) =>
  api.get<InvestmentOperation[]>(
    `/api/investments/operations${accountId ? `?account_id=${accountId}` : ""}`
  );

export const createOperation = (data: OperationCreate) =>
  api.post<InvestmentOperation>("/api/investments/operations", data);

export const getSummary = () =>
  api.get<InvestmentSummary>("/api/investments/summary");

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
