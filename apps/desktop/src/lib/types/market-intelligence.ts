// apps/desktop/src/lib/types/market-intelligence.ts

export interface MacroHistoryPointMI {
  period: string;
  value: number;
}

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
  display_name?: string;
  description?: string;
  subcategory?: string;
  frequency?: string;
  priority?: string;
  previous_value?: number | null;
  delta?: number | null;
  history?: MacroHistoryPointMI[];
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
  display_name?: string;
  display_country?: string;
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
  signal: "positive" | "negative" | "neutral" | "warning" | "no_data";
  signal_text: string;
  source_ids: string[];
}

export interface PersonalImpactMI {
  generated_at: string;
  comparatives: ImpactComparative[];
  warnings: string[];
}

export interface PersonalInflationCategoryMI {
  category: string;
  current: number;
  previous: number;
  yoy_pct: number | null;
}

export interface PersonalEconomyMI {
  generated_at: string;
  personal_inflation: {
    user_yoy_pct: number | null;
    ipc_general: number | null;
    ipc_subyacente: number | null;
    current_total: number;
    previous_total: number;
    by_category: PersonalInflationCategoryMI[];
  };
  real_salary: {
    monthly_now: number | null;
    monthly_year_ago: number | null;
    nominal_yoy_pct: number | null;
    ipc: number | null;
    real_yoy_pct: number | null;
  };
  savings: {
    idle_liquidity: number;
    tipo_bce: number | null;
    potential_monthly: number | null;
  };
  euribor: {
    value: number | null;
    year_ago: number | null;
    history: { period: string; value: number }[];
  };
  fiscal_calendar: {
    date: string;
    label: string;
    audience: "todos" | "autonomos";
    days_left: number;
  }[];
  relevant_news: {
    id: string;
    title: string | null;
    published_at: string;
    source_name: string | null;
    url: string | null;
    matched: string[];
  }[];
}

export interface IngestResultDetail {
  indicator: string;
  category: string;
  provider: string;
  success: boolean;
  fallback_used: boolean;
  error: string | null;
}

export interface IngestStatus {
  status: "idle" | "running" | "done" | "error";
  last_run: string | null;
  count: number;
  results?: IngestResultDetail[];
  storage?: "file" | "memory";
  storage_warning?: string;
}
