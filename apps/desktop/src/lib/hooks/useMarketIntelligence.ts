// apps/desktop/src/lib/hooks/useMarketIntelligence.ts
import { useCallback, useEffect, useState } from "react";
import {
  getMarketSnapshot,
  getForexSnapshot,
  getBondSnapshot,
  getEconomyOverview,
  getIngestStatus,
} from "@/lib/api/market-intelligence";
import type {
  BondSnapshotMI,
  EconomyOverviewMI,
  ForexSnapshotMI,
  IngestStatus,
  IngestStatusRaw,
  MarketSnapshotMI,
} from "@/lib/types/market-intelligence";

const USER_SAFE_MARKET_ERROR =
  "No se han podido actualizar los datos ahora. Se muestran los ultimos datos disponibles si existen.";
const USER_SAFE_ECONOMY_ERROR =
  "No se han podido actualizar los indicadores ahora. Se muestran los ultimos datos disponibles si existen.";

const POLL_MS = 3000;

// ECO-6: la UI consume una VM normalizada; el endpoint devuelve current/last_run (ECO-5).
function normalizeIngestStatus(raw: IngestStatusRaw): IngestStatus {
  const running = raw.current != null;
  const errored = Boolean(raw.last_run?.error);
  const phase: IngestStatus["phase"] = running
    ? "running"
    : errored
      ? "error"
      : raw.last_run
        ? "done"
        : "idle";
  return {
    phase,
    running,
    last_run_at: raw.last_run?.finished_at ?? null,
    results: (raw.last_run?.results ?? []).map((r) => ({
      indicator: r.indicator,
      category: r.category,
      provider: r.provider,
      success: r.status === "ok",
      fallback_used: r.fallback_used,
      error: r.error,
    })),
    storage: raw.storage,
    storage_warning: raw.storage_warning,
  };
}

/** Polling del estado de ingesta: mientras corre sigue preguntando; al terminar
 *  dispara un refetch para pintar el dato fresco. Los snapshots NO esperan a la
 *  ingesta: se cargan de inmediato desde la caché DuckDB. */
function useIngestPolling(onSettled: (status: IngestStatus) => void) {
  const [ingestStatus, setIngestStatus] = useState<IngestStatus | null>(null);

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | null = null;
    let cancelled = false;
    const poll = async () => {
      try {
        const status = normalizeIngestStatus(await getIngestStatus());
        if (cancelled) return;
        setIngestStatus(status);
        if (status.running) {
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

// ponytail: caché a nivel de módulo por clave — sobrevive al desmontaje al cambiar de
// pestaña, así la vista repinta el último dato bueno al instante y revalida detrás.
const cache: Record<string, unknown> = {};

/** ECO-6: hook genérico de recurso MI (caché + polling de ingesta + error honesto).
 *  Unifica lo que antes duplicaban useEconomyMI y useMarketsMI. `load` devuelve el
 *  dato o null; un null nunca pisa un dato bueno previo. */
function useMIResource<T>(key: string, load: () => Promise<T | null>, errorMsg: string) {
  const [data, setData] = useState<T | null>((cache[key] as T) ?? null);
  const [loading, setLoading] = useState(cache[key] == null);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    const next = await load();
    if (next) setData((cache[key] = next) as T);
    setError(next ? null : errorMsg);
    setLoading(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  const ingestStatus = useIngestPolling((status) => {
    if (status.phase === "error") {
      setError("La ingesta de datos fallo; mostrando datos disponibles en cache.");
    }
    refetch();
  });

  return { data, loading, error, ingestStatus, refetch };
}

export function useEconomyMI() {
  const { data, loading, error, ingestStatus } = useMIResource<EconomyOverviewMI>(
    "economy",
    () => getEconomyOverview().catch(() => null),
    USER_SAFE_ECONOMY_ERROR
  );
  return { overview: data, ingestStatus, loading, error };
}

interface MarketsBundle {
  market: MarketSnapshotMI;
  forex: ForexSnapshotMI;
  bonds: BondSnapshotMI;
}

export function useMarketsMI() {
  const { data, loading, error, ingestStatus, refetch } = useMIResource<MarketsBundle>(
    "markets",
    async () => {
      const [market, forex, bonds] = await Promise.all([
        getMarketSnapshot().catch(() => null),
        getForexSnapshot().catch(() => null),
        getBondSnapshot().catch(() => null),
      ]);
      // El mercado manda: sin él consideramos el bundle fallido (conserva el último bueno).
      return market ? { market, forex: forex!, bonds: bonds! } : null;
    },
    USER_SAFE_MARKET_ERROR
  );
  return {
    market: data?.market ?? null,
    forex: data?.forex ?? null,
    bonds: data?.bonds ?? null,
    ingestStatus,
    loading,
    error,
    refetch,
  };
}
