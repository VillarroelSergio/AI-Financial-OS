export type InsightSeverity = "positive" | "info" | "warning" | "critical";
export type InsightType =
  | "spending_anomaly"
  | "monthly_comparison"
  | "savings_rate"
  | "cashflow_alert"
  | "net_worth_change"
  | "investment_allocation"
  | "portfolio_concentration"
  | "wealth_concentration"
  | "goal_progress"
  | "market_context"
  | "macro_context"
  | "data_quality"
  // INS-5 (Lote 1: planificación)
  | "budget_alert"
  | "upcoming_cashflow"
  | "recurring_creep"
  | "household_bill_anomaly"
  | "snapshot_pending"
  // INS-6 (Lote 2: tendencias y patrimonio)
  | "savings_rate_trend"
  | "category_trend"
  | "emergency_fund_coverage"
  | "real_return";
export type InsightClass = "signal" | "context" | "data_quality";
export type DataStatus = "complete" | "partial" | "insufficient" | "empty" | "error";

export interface InsightMetric {
  label: string;
  value: number;
  unit: string;
  precision?: number;
}

export interface InsightSource {
  type: string;
  label: string;
  period?: string;
  source: string;
  updated_at?: string;
}

export interface InsightAction {
  label: string;
  target: string;
  params: Record<string, string>;
}

export interface Insight {
  id: string;
  type: InsightType;
  insight_class: InsightClass;
  dedupe_key: string;
  severity: InsightSeverity;
  title: string;
  summary: string;
  detail?: string;
  period: string;
  impact_area: string;
  status: string;
  confidence: number;
  priority: number;
  data_status: DataStatus;
  primary_metric?: InsightMetric;
  secondary_metrics: InsightMetric[];
  sources: InsightSource[];
  actions: InsightAction[];
  created_at: string;
}

export interface InsightsSummaryCount {
  total: number;
  positive: number;
  info: number;
  warning: number;
  critical: number;
  partial: number;
  insufficient: number;
}

export interface InsightsSummary {
  period: string;
  generated_at: string;
  data_status: DataStatus;
  insights: Insight[];
  summary: InsightsSummaryCount;
}

export interface MonthlyReview {
  period: string;
  headline: string;
  summary: string;
  income: number;
  expenses: number;
  savings: number;
  savings_rate: number;
  net_worth_change?: { amount: number; percentage: number };
  top_positive: Insight[];
  top_warnings: Insight[];
  top_changes: Insight[];
  data_status: DataStatus;
  sources: InsightSource[];
}

export interface AnomaliesResponse {
  period: string;
  baseline_months: number;
  data_status: DataStatus;
  anomalies: Insight[];
}

export interface InsightsParams {
  period?: string;
  type?: InsightType;
  severity?: InsightSeverity;
  impact_area?: string;
  limit?: number;
  include_dismissed?: boolean;
}
