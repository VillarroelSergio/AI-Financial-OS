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

const USER_SAFE_MARKET_ERROR =
  "No se han podido actualizar los datos ahora. Se muestran los ultimos datos disponibles si existen.";
const USER_SAFE_ECONOMY_ERROR =
  "No se han podido actualizar los indicadores ahora. Se muestran los ultimos datos disponibles si existen.";

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
        getPersonalImpact().catch(() => null),
      ]);
      setMacro(macroData);
      setImpact(impactData);
      setError(null);
    } catch {
      setError(USER_SAFE_ECONOMY_ERROR);
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

  const loadSnapshots = useCallback(async () => {
    try {
      const [marketData, forexData, bondsData] = await Promise.all([
        getMarketSnapshot(),
        getForexSnapshot(),
        getBondSnapshot(),
      ]);
      setMarket(marketData);
      setForex(forexData);
      setBonds(bondsData);
      setError(null);
    } catch {
      setError(USER_SAFE_MARKET_ERROR);
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
            setError("La ingesta de datos fallo; mostrando datos disponibles en cache.");
          }
          await loadSnapshots();
        }
      } catch {
        await loadSnapshots();
      }
    };
    poll();
    return () => {
      if (pollRef.current) clearTimeout(pollRef.current);
    };
  }, [loadSnapshots]);

  return { market, forex, bonds, ingestStatus, loading, error };
}
