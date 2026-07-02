import { useCallback, useState } from "react";
import { runAudit } from "@/lib/api/price-coverage";
import type { AuditReport } from "@/lib/types/price-coverage";

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
