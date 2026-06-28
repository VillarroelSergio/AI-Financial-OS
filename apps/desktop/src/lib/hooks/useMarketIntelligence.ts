// apps/desktop/src/lib/hooks/useMarketIntelligence.ts
import { useCallback, useEffect, useRef, useState } from "react";
import {
  getMacroSnapshot,
  getMarketSnapshot,
  getForexSnapshot,
  getBondSnapshot,
  getPersonalImpact,
  getIngestStatus,
} from "@/lib/api/market-intelligence";
import type {
  BondSnapshotMI,
  ForexSnapshotMI,
  IngestStatus,
  MacroSnapshotMI,
  MarketSnapshotMI,
  PersonalImpactMI,
} from "@/lib/types/market-intelligence";

export function useEconomyMI() {
  const [macro, setMacro] = useState<MacroSnapshotMI | null>(null);
  const [impact, setImpact] = useState<PersonalImpactMI | null>(null);
  const [ingestStatus, setIngestStatus] = useState<IngestStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = useCallback(async () => {
    const [macroResult, impactResult] = await Promise.allSettled([
      getMacroSnapshot(),
      getPersonalImpact(),
    ]);

    if (macroResult.status === "fulfilled") setMacro(macroResult.value);
    if (impactResult.status === "fulfilled") setImpact(impactResult.value);

    if (macroResult.status === "rejected" && impactResult.status === "rejected") {
      const reason = macroResult.reason;
      setError(reason instanceof Error ? reason.message : "Error al cargar datos economicos");
    } else if (impactResult.status === "rejected") {
      setError("No se pudo calcular el impacto personal; mostrando indicadores macro disponibles.");
    } else {
      setError(null);
    }

    setLoading(false);
  }, []);

  useEffect(() => {
    const poll = async () => {
      try {
        const status = await getIngestStatus();
        setIngestStatus(status);
        if (status.status === "running" || status.status === "idle") {
          pollRef.current = setTimeout(poll, 3000);
        } else {
          if (status.status === "error") {
            setError("La ingesta de datos fallo; mostrando datos disponibles en cache.");
          }
          await load();
        }
      } catch {
        await load();
      }
    };
    poll();
    return () => {
      if (pollRef.current) clearTimeout(pollRef.current);
    };
  }, [load]);

  return { macro, impact, ingestStatus, loading, error };
}

export function useMarketsMI() {
  const [market, setMarket] = useState<MarketSnapshotMI | null>(null);
  const [forex, setForex] = useState<ForexSnapshotMI | null>(null);
  const [bonds, setBonds] = useState<BondSnapshotMI | null>(null);
  const [ingestStatus, setIngestStatus] = useState<IngestStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    const poll = async () => {
      try {
        const status = await getIngestStatus();
        setIngestStatus(status);
        if (status.status === "running" || status.status === "idle") {
          pollRef.current = setTimeout(poll, 3000);
        } else {
          if (status.status === "error") {
            setError("La ingesta de datos fallo; mostrando datos disponibles en cache.");
          }

          const [marketResult, forexResult, bondsResult] = await Promise.allSettled([
            getMarketSnapshot(),
            getForexSnapshot(),
            getBondSnapshot(),
          ]);

          if (marketResult.status === "fulfilled") setMarket(marketResult.value);
          if (forexResult.status === "fulfilled") setForex(forexResult.value);
          if (bondsResult.status === "fulfilled") setBonds(bondsResult.value);

          if ([marketResult, forexResult, bondsResult].every((r) => r.status === "rejected")) {
            const reason = marketResult.status === "rejected" ? marketResult.reason : null;
            setError(reason instanceof Error ? reason.message : "Error al cargar datos de mercado");
          } else if ([marketResult, forexResult, bondsResult].some((r) => r.status === "rejected")) {
            setError("Algunas fuentes de mercado no respondieron; mostrando datos disponibles.");
          } else {
            setError(null);
          }

          setLoading(false);
        }
      } catch {
        setLoading(false);
      }
    };
    poll();
    return () => {
      if (pollRef.current) clearTimeout(pollRef.current);
    };
  }, []);

  return { market, forex, bonds, ingestStatus, loading, error };
}
