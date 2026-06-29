export type CoverageStatus =
  | "OK"
  | "FX_PENDING"
  | "AMBIGUOUS"
  | "UNAVAILABLE"
  | "MANUAL"
  | "ERROR";

export interface TickerCandidate {
  ticker: string;
  yfinance_symbol: string;
  name: string;
  exchange: string;
  currency: string;
  asset_type: string;
  confidence: number;
}

export interface AssetResolutionResponse {
  asset_name: string;
  candidates: TickerCandidate[];
  selected: TickerCandidate | null;
  status: string;
}

export interface CoverageAsset {
  asset_name: string;
  selected_ticker: string | null;
  exchange: string | null;
  currency: string | null;
  provider: string | null;
  price: number | null;
  price_currency: string | null;
  requires_fx_conversion: boolean;
  last_update: string | null;
  freshness_hours: number | null;
  from_cache: boolean;
  status: CoverageStatus;
  confidence: number;
  notes: string[];
  // FX / EUR valuation
  fx_rate: number | null;
  fx_currency_pair: string | null;
  eur_price: number | null;
  fx_updated_at: string | null;
}

export interface AuditSummary {
  total: number;
  with_price: number;
  eur_valued: number;
  fx_pending: number;
  ambiguous: number;
  manual: number;
  unavailable: number;
  error: number;
}

export interface AuditReport {
  generated_at: string;
  summary: AuditSummary;
  assets: CoverageAsset[];
}
