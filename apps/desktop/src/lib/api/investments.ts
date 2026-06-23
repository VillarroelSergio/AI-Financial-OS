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
