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
    try {
      const [macroData, impactData] = await Promise.all([
        getMacroSnapshot(),
        getPersonalImpact(),
      ]);
      setMacro(macroData);
      setImpact(impactData);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al cargar datos económicos");
    } finally {
      setLoading(false);
    }
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
            setError("La ingesta de datos falló; mostrando datos disponibles en caché.");
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
            setError("La ingesta de datos falló; mostrando datos disponibles en caché.");
          }
          try {
            const [marketData, forexData, bondsData] = await Promise.all([
              getMarketSnapshot(),
              getForexSnapshot(),
              getBondSnapshot(),
            ]);
            setMarket(marketData);
            setForex(forexData);
            setBonds(bondsData);
          } catch (e) {
            setError(e instanceof Error ? e.message : "Error al cargar datos de mercado");
          } finally {
            setLoading(false);
          }
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
