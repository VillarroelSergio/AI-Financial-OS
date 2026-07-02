// apps/desktop/src/lib/hooks/useFinancialKnowledge.ts
import { useCallback, useState } from "react";
import {
  getKnowledgeSnapshot,
  getMarketRegime,
  getFinancialSignals,
  getPersonalImpactFK,
  getAIDatasheet,
  recomputeKnowledge,
} from "@/lib/api/financial-knowledge";
import { useAsyncData } from "@/lib/hooks/useAsyncData";
import type {
  AIDatasheet,
  FinancialSignal,
  KnowledgeSnapshot,
  MarketRegime,
  PersonalImpactFK,
  RecomputeResult,
} from "@/lib/types/financial-knowledge";

export function useKnowledgeSnapshot() {
  return useAsyncData<KnowledgeSnapshot>(getKnowledgeSnapshot);
}

export function useMarketRegime() {
  return useAsyncData<MarketRegime>(getMarketRegime);
}

export function useFinancialSignals() {
  return useAsyncData<FinancialSignal[]>(getFinancialSignals);
}

export function usePersonalImpactFK() {
  return useAsyncData<PersonalImpactFK[]>(getPersonalImpactFK);
}

export function useAIDatasheet() {
  return useAsyncData<AIDatasheet>(getAIDatasheet);
}

export function useRecompute() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<RecomputeResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const recompute = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setResult(await recomputeKnowledge());
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al recomputar");
    } finally {
      setLoading(false);
    }
  }, []);

  return { recompute, loading, result, error };
}
