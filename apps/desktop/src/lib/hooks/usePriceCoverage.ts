import { useCallback, useState } from "react";
import { runAudit, resolveAsset } from "@/lib/api/price-coverage";
import type { AuditReport, AssetResolutionResponse } from "@/lib/types/price-coverage";

export function usePriceCoverage() {
  const [report, setReport] = useState<AuditReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const audit = useCallback(async (assets: { name: string }[] = []) => {
    setLoading(true);
    setError(null);
    try {
      const result = await runAudit(assets);
      setReport(result);
      return result;
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error al auditar cobertura");
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { report, loading, error, audit };
}

export function useAssetResolve() {
  const [resolution, setResolution] = useState<AssetResolutionResponse | null>(null);
  const [loading, setLoading] = useState(false);

  const resolve = useCallback(async (assetName: string) => {
    setLoading(true);
    try {
      const result = await resolveAsset(assetName);
      setResolution(result);
      return result;
    } finally {
      setLoading(false);
    }
  }, []);

  return { resolution, loading, resolve };
}
