// apps/desktop/src/lib/types/financial-knowledge.ts

export type Trend = "rising" | "falling" | "stable" | "unknown";
export type Severity = "low" | "medium" | "high" | "critical";
export type Direction = "positive" | "negative" | "mixed" | "neutral";
export type RiskLevel = "risk_on" | "risk_off" | "neutral";
export type InflationRegime = "inflationary" | "disinflationary" | "deflationary" | "stable";
export type RatesRegime = "high_rates" | "low_rates" | "cutting_cycle" | "hiking_cycle" | "stable";
export type GrowthRegime = "expansion" | "slowdown" | "recession_risk" | "unknown";
export type MarketTrend = "bull" | "bear" | "sideways" | "unknown";

export interface EconomicIndicatorInsight {
  id: string;
  indicator_id: string;
  name: string;
  category: string;
  country: string;
  value: number;
  unit: string;
  period: string;
  trend: Trend;
  severity: Severity;
  quality_score: number;
  computed_at: string;
  previous_value?: number;
  change_abs?: number;
  change_pct?: number;
  target_value?: number;
  distance_to_target?: number;
  interpretation?: string;
  source_provider?: string;
}

export interface FinancialSignal {
  id: string;
  signal_type: string;
  name: string;
  category: string;
  description: string;
  direction: Direction;
  severity: Severity;
  confidence_score: number;
  quality_score: number;
  computed_at: string;
  affected_assets: string[];
  affected_user_domains: string[];
  source_indicators: string[];
  rule_id?: string;
}

export interface MarketRegime {
  id: string;
  risk_level: RiskLevel;
  inflation_regime: InflationRegime;
  rates_regime: RatesRegime;
  growth_regime: GrowthRegime;
  market_trend: MarketTrend;
  confidence_score: number;
  explanation: string;
  computed_at: string;
  signals_used: string[];
}

export interface PersonalImpactFK {
  id: string;
  impact_type: string;
  user_domain: string;
  title: string;
  description: string;
  severity: Severity;
  confidence_score: number;
  computed_at: string;
  estimated_monthly_impact?: number;
  estimated_portfolio_impact?: number;
  currency: string;
  related_accounts: string[];
  related_holdings: string[];
  related_goals: string[];
  source_signals: string[];
}

export interface AIDatasheet {
  generated_at: string;
  quality_score: number;
  market_regime?: Record<string, unknown>;
  macro_insights: Record<string, unknown>[];
  financial_signals: Record<string, unknown>[];
  personal_impacts: Record<string, unknown>[];
  portfolio_context: Record<string, unknown>;
  news_context: Record<string, unknown>[];
  warnings: string[];
  sources: string[];
}

export interface KnowledgeSnapshot {
  generated_at: string;
  quality_score: number;
  regime?: MarketRegime;
  signals: FinancialSignal[];
  insights: EconomicIndicatorInsight[];
  personal_impacts: PersonalImpactFK[];
  warnings: string[];
}

export interface RecomputeResult {
  success: boolean;
  message: string;
  insights_computed: number;
  signals_computed: number;
  regime_computed: boolean;
  impacts_computed: number;
  datasheet_generated: boolean;
  errors: string[];
}
