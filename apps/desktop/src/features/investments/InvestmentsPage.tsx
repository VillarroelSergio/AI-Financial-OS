import { useState } from "react";
import { Plus, RefreshCw } from "lucide-react";
import EmptyState from "@/components/ui/EmptyState";
import MetricCard from "@/components/ui/MetricCard";
import Spinner from "@/components/ui/Spinner";
import { useAccounts } from "@/lib/hooks/useAccounts";
import { useHoldings, useInvestmentSummary, useRefreshPrices } from "@/lib/hooks/useInvestments";
import { formatCurrency } from "@/lib/formatters/currency";
import DistributionChart from "./components/DistributionChart";
import PositionsTabs from "./components/PositionsTabs";
import ManualNavDialog from "./components/ManualNavDialog";
import AddStockDialog from "./components/AddStockDialog";
import AddFundDialog from "./components/AddFundDialog";
import AddSavingsDialog from "./components/AddSavingsDialog";
import HoldingEditor from "./components/HoldingEditor";
import type { HoldingEnriched } from "@/lib/types";

export default function InvestmentsPage() {
  const demoEmpty = new URLSearchParams(window.location.search).get("demo") === "empty";
  const { summary, loading: summaryLoading, refresh: refreshSummary } = useInvestmentSummary();
  const { holdings, loading: holdingsLoading, refresh: refreshHoldings, remove } = useHoldings();
  const { accounts } = useAccounts();

  const onRefreshAll = () => {
    refreshSummary();
    refreshHoldings();
  };

  const { refresh: triggerRefresh, refreshing, result: refreshResult, needsManualNav, clearNeedsManualNav, clearResult } =
    useRefreshPrices(onRefreshAll);

  const [addStock, setAddStock] = useState(false);
  const [addFund, setAddFund] = useState(false);
  const [addSavings, setAddSavings] = useState(false);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingHolding, setEditingHolding] = useState<HoldingEnriched | null>(null);

  const trAccounts = accounts.filter((a) => a.type === "broker");
  const finizensAccounts = accounts.filter((a) => a.type === "investment");
  const ahorroAccounts = accounts.filter((a) => a.type === "savings");

  const trId = trAccounts[0]?.id ?? "";
  const finizensId = finizensAccounts[0]?.id ?? "";
  const ahorroId = ahorroAccounts[0]?.id ?? "";

  const accountNames: Record<string, string> = {
    ...Object.fromEntries(accounts.map((a) => [a.id, a.name])),
  };

  const navHoldings = holdings.filter((h) => needsManualNav.includes(h.id));

  const loading = summaryLoading || holdingsLoading;

  const lastUpdated = summary?.last_updated
    ? new Date(summary.last_updated).toLocaleString("es-ES", {
        day: "2-digit",
        month: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
      })
    : null;

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <Spinner />
      </div>
    );
  }

  const hasHoldings = !demoEmpty && holdings.length > 0;
  const realHoldings = holdings.filter((h) => !h.is_mock);
  const returnPct = summary?.return_percent ?? 0;
  const isPositive = returnPct >= 0;
  const openAdd = () => {
    setEditingHolding(null);
    setEditorOpen(true);
  };
  const openEdit = (holding: HoldingEnriched) => {
    setEditingHolding(holding);
    setEditorOpen(true);
  };
  const deleteHolding = async (holding: HoldingEnriched) => {
    await remove(holding.id);
    onRefreshAll();
  };

  return (
    <div className="p-2xl space-y-xl">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-display-lg text-on-dark">Inversiones</h1>
          {lastUpdated && (
            <p className="text-caption text-stone mt-xs">Última actualización: {lastUpdated}</p>
          )}
        </div>
        <div className="flex items-center gap-sm">
          <button onClick={openAdd} className="flex items-center gap-sm px-md py-sm rounded-full bg-primary text-on-primary text-body-sm hover:bg-primary/90 transition-colors">
            <Plus size={14} />
            Anadir activo
          </button>
          <button
            onClick={triggerRefresh}
            disabled={refreshing}
            className="flex items-center gap-sm px-md py-sm rounded-full border border-hairline-dark text-body-sm text-stone hover:text-on-dark hover:border-on-dark transition-colors disabled:opacity-50"
          >
            <RefreshCw size={14} className={refreshing ? "animate-spin" : ""} />
            {refreshing ? "Actualizando..." : "Actualizar precios"}
          </button>
        </div>
      </div>

      {editorOpen && (
        <HoldingEditor
          holding={editingHolding}
          accounts={accounts}
          onClose={() => setEditorOpen(false)}
          onSaved={onRefreshAll}
        />
      )}

      {refreshResult && (
        <div className="rounded-md border border-hairline-dark bg-surface-elevated p-lg">
          <div className="flex items-start justify-between gap-md">
            <div>
              <p className="text-body-sm font-semibold text-on-dark">
                {refreshResult.errors.length ? "Actualizacion parcial de precios" : "Precios revisados"}
              </p>
              <p className="mt-xs text-caption text-stone">
                {refreshResult.updated} actualizados · {refreshResult.manual_required.length} requieren precio manual · {refreshResult.skipped.length} omitidos como efectivo/ahorro.
              </p>
              {refreshResult.manual_required.length > 0 && (
                <p className="mt-xs text-caption text-mute">Precio manual: precio introducido por ti cuando no hay proveedor automatico.</p>
              )}
            </div>
            <div className="flex shrink-0 gap-sm">
              <button onClick={clearResult} className="rounded-full border border-hairline-dark px-md py-xs text-caption text-stone hover:text-on-dark">
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}

      {!hasHoldings ? (
        <EmptyState
          title="Sin posiciones"
          description="Añade tus primeras inversiones para ver el estado de tu cartera."
          action={
            <button
              onClick={openAdd}
              className="px-lg py-sm rounded-md text-body-sm bg-primary text-on-primary hover:bg-primary/90 transition-colors"
            >
              Anadir activo
            </button>
          }
        />
      ) : (
        <>
          {/* Metric cards */}
          {summary && (
            <div className="grid grid-cols-3 gap-xl">
              <MetricCard label="Valor total" value={formatCurrency(summary.total_value)} />
              <MetricCard label="Aportado" value={formatCurrency(summary.total_invested)} />
              <MetricCard
                label="Rentabilidad"
                value={formatCurrency(summary.return_absolute)}
                delta={`${isPositive ? "+" : ""}${returnPct.toFixed(2)}%`}
                deltaPositive={isPositive}
              />
            </div>
          )}

          {/* Chart + positions */}
          <div className="grid grid-cols-5 gap-xl">
            <div className="col-span-3">
              <DistributionChart holdings={realHoldings} accountNames={accountNames} />
            </div>
            <div className="col-span-2">
              <PositionsTabs
                holdings={holdings}
                trAccountIds={trAccounts.map((a) => a.id)}
                finizensAccountIds={finizensAccounts.map((a) => a.id)}
                ahorroAccountIds={ahorroAccounts.map((a) => a.id)}
                onAddStock={openAdd}
                onAddFund={() => setAddFund(true)}
                onAddSavings={() => setAddSavings(true)}
                onEdit={openEdit}
                onDelete={deleteHolding}
              />
            </div>
          </div>
        </>
      )}

      {/* Dialogs */}
      <AddStockDialog
        open={addStock}
        accountId={trId}
        onClose={() => setAddStock(false)}
        onSuccess={onRefreshAll}
      />
      <AddFundDialog
        open={addFund}
        accountId={finizensId}
        onClose={() => setAddFund(false)}
        onSuccess={onRefreshAll}
      />
      <AddSavingsDialog
        open={addSavings}
        accountId={ahorroId}
        onClose={() => setAddSavings(false)}
        onSuccess={onRefreshAll}
      />
      <ManualNavDialog
        open={navHoldings.length > 0}
        holdings={navHoldings}
        onClose={clearNeedsManualNav}
        onSuccess={onRefreshAll}
      />
    </div>
  );
}
