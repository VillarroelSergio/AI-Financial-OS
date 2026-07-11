import { api } from "@/lib/api/client";
import { buildQueryString } from "@/lib/api/queryParams";
import type {
  AnomaliesResponse,
  InsightsSummary,
  InsightsParams,
  MonthlyReview,
} from "../types/insights.types";

export const getInsights = (params: InsightsParams = {}): Promise<InsightsSummary> =>
  api.get<InsightsSummary>(`/api/insights${buildQueryString(params as Record<string, string | number | boolean | undefined>)}`);

export const getMonthlyReview = (period?: string): Promise<MonthlyReview> =>
  api.get<MonthlyReview>(`/api/insights/monthly-review${buildQueryString({ period })}`);

export const getAnomalies = (period?: string, baselineMonths?: number): Promise<AnomaliesResponse> =>
  api.get<AnomaliesResponse>(`/api/insights/anomalies${buildQueryString({ period, baseline_months: baselineMonths })}`);

export const getDataQualityInsights = (period?: string): Promise<InsightsSummary> =>
  api.get<InsightsSummary>(`/api/insights/data-quality${buildQueryString({ period })}`);

export const refreshInsights = (period?: string): Promise<InsightsSummary> =>
  api.post<InsightsSummary>(`/api/insights/refresh${buildQueryString({ period })}`, {});

export const dismissInsight = (insightId: string): Promise<{ insight_id: string; dismissed_at: string }> =>
  api.post(`/api/insights/${insightId}/dismiss`, {});

export const restoreInsight = (insightId: string): Promise<{ insight_id: string; restored: boolean }> =>
  api.post(`/api/insights/${insightId}/restore`, {});
