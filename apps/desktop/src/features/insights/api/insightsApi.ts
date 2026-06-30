import { api } from "@/lib/api/client";
import type {
  AnomaliesResponse,
  InsightsSummary,
  InsightsParams,
  MonthlyReview,
} from "../types/insights.types";

function buildParams(params: Record<string, string | number | boolean | undefined>): string {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== null && v !== "") {
      p.set(k, String(v));
    }
  }
  const s = p.toString();
  return s ? `?${s}` : "";
}

export const getInsights = (params: InsightsParams = {}): Promise<InsightsSummary> =>
  api.get<InsightsSummary>(`/api/insights${buildParams(params as Record<string, string | number | boolean | undefined>)}`);

export const getMonthlyReview = (period?: string): Promise<MonthlyReview> =>
  api.get<MonthlyReview>(`/api/insights/monthly-review${period ? `?period=${period}` : ""}`);

export const getAnomalies = (period?: string, baselineMonths?: number): Promise<AnomaliesResponse> =>
  api.get<AnomaliesResponse>(`/api/insights/anomalies${buildParams({ period, baseline_months: baselineMonths })}`);

export const getDataQualityInsights = (period?: string): Promise<InsightsSummary> =>
  api.get<InsightsSummary>(`/api/insights/data-quality${period ? `?period=${period}` : ""}`);

export const refreshInsights = (period?: string): Promise<InsightsSummary> =>
  api.post<InsightsSummary>(`/api/insights/refresh${period ? `?period=${period}` : ""}`, {});

export const dismissInsight = (insightId: string): Promise<{ insight_id: string; dismissed_at: string }> =>
  api.post(`/api/insights/${insightId}/dismiss`, {});
