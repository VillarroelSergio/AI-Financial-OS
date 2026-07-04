import { LineChart } from "lucide-react";
import Spinner from "@/components/ui/Spinner";
import { EmptyState } from "@/components/ui/Dashboard";
import { useHoldings } from "@/lib/hooks/useInvestments";
import PositionTrackingTable from "./PositionTrackingTable";

export default function PositionTrackingPage() {
  const { holdings, loading, error } = useHoldings();

  const tracked = holdings.filter(
    (h) => h.symbol && (h.asset_type === "stock" || h.asset_type === "etf"),
  );

  return (
    <div className="flex flex-col gap-6 p-6 max-w-screen-xl mx-auto">
      <div>
        <h1 className="text-xl font-semibold text-on-dark">Seguimiento de posiciones</h1>
        <p className="text-sm text-mute mt-1">
          Evolucion de cada accion desde tu precio de entrada hasta hoy. Las posiciones nuevas
          aparecen aqui automaticamente al darlas de alta en Inversiones.
        </p>
      </div>

      {loading && (
        <div className="flex justify-center py-16">
          <Spinner />
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {!loading && !error && tracked.length === 0 && (
        <EmptyState
          icon={LineChart}
          title="Sin acciones que seguir"
          description="Da de alta una accion o ETF con ticker en Inversiones y su evolucion aparecera aqui."
        />
      )}

      {!loading && tracked.length > 0 && <PositionTrackingTable holdings={tracked} />}
    </div>
  );
}
