// apps/desktop/src/lib/hooks/useMarketIntelligence.ts
import { useCallback, useEffect, useState } from "react";
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

// ponytail: caché a nivel de módulo — sobrevive al desmontaje al cambiar de
// pestaña, así la vista repinta el último dato bueno al instante y revalida detrás.
const cache: {
  macro: MacroSnapshotMI | null;
  impact: PersonalImpactMI | null;
  market: MarketSnapshotMI | null;
  forex: ForexSnapshotMI | null;
  bonds: BondSnapshotMI | null;
} = { macro: null, impact: null, market: null, forex: null, bonds: null };

const POLL_MS = 3000;

/** Polling del estado de ingesta: mientras corre (o aún no arrancó) sigue
 *  preguntando; cuando termina, dispara un refetch para pintar el dato fresco.
 *  Los snapshots NO esperan a la ingesta: se cargan de inmediato desde caché DuckDB. */
function useIngestPolling(onSettled: (status: IngestStatus) => void) {
  const [ingestStatus, setIngestStatus] = useState<IngestStatus | null>(null);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | null = null;
    let cancelled = false;
    const poll = async () => {
      try {
        const status = await getIngestStatus();
        if (cancelled) return;
        setIngestStatus(status);
        if (status.status === "running" || status.status === "idle") {
          timer = setTimeout(poll, POLL_MS);
        } else {
          onSettled(status);
        }
      } catch {
        // Sin estado de ingesta no bloqueamos nada: los snapshots ya se cargaron.
      }
    };
    poll();
    return () => {
      cancelled = true;
      if (timer) clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return ingestStatus;
}

export function useEconomyMI() {
  const [macro, setMacro] = useState<MacroSnapshotMI | null>(cache.macro);
  const [impact, setImpact] = useState<PersonalImpactMI | null>(cache.impact);
  const [bonds, setBonds] = useState<BondSnapshotMI | null>(cache.bonds);
  const [forex, setForex] = useState<ForexSnapshotMI | null>(cache.forex);
  const [loading, setLoading] = useState(cache.macro === null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const [macroData, impactData, bondsData, forexData] = await Promise.all([
      getMacroSnapshot().catch(() => null),
      getPersonalImpact().catch(() => null),
      getBondSnapshot().catch(() => null),
      getForexSnapshot().catch(() => null),
    ]);
    // Nunca pisar un dato bueno con null: si un fetch falla, se conserva el último válido.
    if (macroData) setMacro((cache.macro = macroData));
    if (impactData) setImpact((cache.impact = impactData));
    if (bondsData) setBonds((cache.bonds = bondsData));
    if (forexData) setForex((cache.forex = forexData));
    setError(macroData ? null : USER_SAFE_ECONOMY_ERROR);
    setLoading(false);
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const ingestStatus = useIngestPolling((status) => {
    if (status.status === "error") {
      setError("La ingesta de datos fallo; mostrando datos disponibles en cache.");
    }
    load();
  });

  return { macro, impact, bonds, forex, ingestStatus, loading, error };
}

export function useMarketsMI() {
  const [market, setMarket] = useState<MarketSnapshotMI | null>(cache.market);
  const [forex, setForex] = useState<ForexSnapshotMI | null>(cache.forex);
  const [bonds, setBonds] = useState<BondSnapshotMI | null>(cache.bonds);
  const [loading, setLoading] = useState(cache.market === null);
  const [error, setError] = useState<string | null>(null);

  const loadSnapshots = useCallback(async () => {
    const [marketData, forexData, bondsData] = await Promise.all([
      getMarketSnapshot().catch(() => null),
      getForexSnapshot().catch(() => null),
      getBondSnapshot().catch(() => null),
    ]);
    if (marketData) setMarket((cache.market = marketData));
    if (forexData) setForex((cache.forex = forexData));
    if (bondsData) setBonds((cache.bonds = bondsData));
    setError(marketData ? null : USER_SAFE_MARKET_ERROR);
    setLoading(false);
  }, []);

  useEffect(() => {
    loadSnapshots();
  }, [loadSnapshots]);

  const ingestStatus = useIngestPolling((status) => {
    if (status.status === "error") {
      setError("La ingesta de datos fallo; mostrando datos disponibles en cache.");
    }
    loadSnapshots();
  });

  return { market, forex, bonds, ingestStatus, loading, error, refetch: loadSnapshots };
}
