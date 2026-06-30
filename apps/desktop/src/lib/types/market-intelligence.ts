// apps/desktop/src/lib/types/market-intelligence.ts

export interface MacroDataPointMI {
  catalog_item_id: string;
  indicator_id?: string;
  country?: string;
  period?: string;
  value?: number;
  unit?: string;
  provider_id?: string;
  quality_score: number;
  data_status?: "ok" | "limited" | "unavailable" | "requires_review";
  retrieved_at?: string | null;
}

export interface MacroSnapshotMI {
  status: "ok" | "partial" | "empty" | "error";
  spain: MacroDataPointMI[];
  eurozone: MacroDataPointMI[];
  usa: MacroDataPointMI[];
  generated_at: string;
  warnings: string[];
}

export interface QuoteMI {
  catalog_item_id: string;
  symbol?: string;
  asset_type?: string;
  price?: number;
  change_pct?: number;
  currency?: string;
  provider_id?: string;
  quality_score: number;
  data_status?: "ok" | "limited" | "unavailable" | "requires_review";
  observed_at?: string | null;
}

export interface MarketSnapshotMI {
  status: "ok" | "partial" | "empty" | "error";
  indices: QuoteMI[];
  crypto: QuoteMI[];
  commodities: QuoteMI[];
  generated_at: string;
  warnings: string[];
  quality_score: number;
}

export interface ForexRateMI {
  catalog_item_id: string;
  base_currency?: string;
  quote_currency?: string;
  rate?: number;
  date?: string;
  provider_id?: string;
  quality_score: number;
  data_status?: "ok" | "limited" | "unavailable";
}

export interface ForexSnapshotMI {
  rates: ForexRateMI[];
  generated_at: string;
  warnings: string[];
}

export interface BondYieldMI {
  catalog_item_id: string;
  country?: string;
  maturity?: string;
  yield_value?: number;
  date?: string;
  provider_id?: string;
  quality_score: number;
  data_status?: "ok" | "limited" | "unavailable";
}

export interface BondSnapshotMI {
  yields: BondYieldMI[];
  generated_at: string;
  warnings: string[];
}

export interface ImpactComparative {
  id: string;
  title: string;
  description: string;
  market_value: number | null;
  market_label: string;
  personal_value: number | null;
  personal_label: string;
  signal: "positive" | "negative" | "neutral" | "warning";
  signal_text: string;
  source_ids: string[];
}

export interface PersonalImpactMI {
  generated_at: string;
  comparatives: ImpactComparative[];
  warnings: string[];
}

export interface IngestStatus {
  status: "idle" | "running" | "done" | "error";
  last_run: string | null;
  count: number;
}
