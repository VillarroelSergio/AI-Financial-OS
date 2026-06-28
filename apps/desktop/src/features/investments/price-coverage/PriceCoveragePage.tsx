import { useCallback, useEffect } from "react";
import { RefreshCw } from "lucide-react";
import Spinner from "@/components/ui/Spinner";
import { usePriceCoverage } from "@/lib/hooks/usePriceCoverage";
import PriceCoverageSummaryCards from "./PriceCoverageSummaryCards";
import PriceCoverageTable from "./PriceCoverageTable";

export default function PriceCoveragePage() {
  const { report, loading, error, audit } = usePriceCoverage();

  useEffect(() => {
    audit();
  }, [audit]);

  const handleRetry = useCallback(
    (assetName: string) => {
      audit([{ name: assetName }]);
    },
    [audit],
  );

  return (
    <div className="flex flex-col gap-6 p-6 max-w-screen-xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-semibold text-on-dark">Cobertura de precios</h1>
          <p className="text-sm text-mute mt-1">
            Comprueba si tus acciones pueden actualizarse automaticamente con los proveedores
            actuales.
          </p>
        </div>
        <button
          onClick={() => audit()}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-white text-sm font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
        >
          <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
          Auditar
        </button>
      </div>

      {/* Summary cards */}
      {report && <PriceCoverageSummaryCards summary={report.summary} />}

      {/* Loading (first load only) */}
      {loading && !report && (
        <div className="flex justify-center py-16">
          <Spinner />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Table */}
      {report && <PriceCoverageTable assets={report.assets} onRetry={handleRetry} />}

      {/* Timestamp */}
      {report && (
        <p className="text-xs text-mute">
          Generado el{" "}
          {new Date(report.generated_at).toLocaleString("es-ES", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          })}
        </p>
      )}
    </div>
  );
}
