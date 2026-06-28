// apps/desktop/src/lib/api/financial-knowledge.ts
import { api } from "./client";
import type {
  AIDatasheet,
  FinancialSignal,
  KnowledgeSnapshot,
  MarketRegime,
  PersonalImpactFK,
  RecomputeResult,
} from "@/lib/types/financial-knowledge";

export const getKnowledgeSnapshot = () =>
  api.get<KnowledgeSnapshot>("/api/financial-knowledge/snapshot");

export const getMarketRegime = () =>
  api.get<MarketRegime>("/api/financial-knowledge/regime");

export const getFinancialSignals = () =>
  api.get<FinancialSignal[]>("/api/financial-knowledge/signals");

export const getPersonalImpactFK = () =>
  api.get<PersonalImpactFK[]>("/api/financial-knowledge/personal-impact");

export const getAIDatasheet = () =>
  api.get<AIDatasheet>("/api/financial-knowledge/datasheet");

export const recomputeKnowledge = () =>
  api.post<RecomputeResult>("/api/financial-knowledge/recompute", {});
