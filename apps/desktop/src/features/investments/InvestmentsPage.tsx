import { useState } from "react";
import { RefreshCw } from "lucide-react";
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

export default function InvestmentsPage() {
  const { summary, loading: summaryLoading, refresh: refreshSummary } = useInvestmentSummary();
  const { holdings, loading: holdingsLoading, refresh: refreshHoldings } = useHoldings();
  const { accounts } = useAccounts();

  const onRefreshAll = () => {
    refreshSummary();
    refreshHoldings();
  };

  const { refresh: triggerRefresh, refreshing, needsManualNav, clearNeedsManualNav } =
    useRefreshPrices(onRefreshAll);

  const [addStock, setAddStock] = useState(false);
  const [addFund, setAddFund] = useState(false);
  const [addSavings, setAddSavings] = useState(false);

  const trAccounts = accounts.filter((a) => a.type === "broker");
  const finizensAccounts = accounts.filter((a) => a.type === "investment");
  const ahorroAccounts = accounts.filter((a) => a.type === "savings");

  const trId = trAccounts[0]?.id ?? "";
  const finizensId = finizensAccounts[0]?.id ?? "";
  const ahorroId = ahorroAccounts[0]?.id ?? "";

  const accountNames: Record<string, string> = {
    ...Object.fromEntries(trAccounts.map((a) => [a.id, "Trade Republic"])),
    ...Object.fromEntries(finizensAccounts.map((a) => [a.id, "Finizens"])),
    ...Object.fromEntries(ahorroAccounts.map((a) => [a.id, "Ahorro"])),
  };

  const navHoldings = holdings.filter((h) => needsManualNav.includes(h.asset_id));

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

  const hasHoldings = holdings.length > 0;
  const returnPct = summary?.return_percent ?? 0;
  const isPositive = returnPct >= 0;

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
        <button
          onClick={triggerRefresh}
          disabled={refreshing}
          className="flex items-center gap-sm px-md py-sm rounded-full border border-hairline-dark text-body-sm text-stone hover:text-on-dark hover:border-on-dark transition-colors disabled:opacity-50"
        >
          <RefreshCw size={14} className={refreshing ? "animate-spin" : ""} />
          {refreshing ? "Actualizando..." : "Actualizar precios"}
        </button>
      </div>

      {!hasHoldings ? (
        <EmptyState
          title="Sin posiciones"
          description="Añade tus primeras inversiones para ver el estado de tu cartera."
          action={
            <button
              onClick={() => setAddStock(true)}
              className="px-lg py-sm rounded-md text-body-sm bg-primary text-on-primary hover:bg-primary/90 transition-colors"
            >
              Añadir acción
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
              {summary && (
                <DistributionChart
                  byAccount={summary.by_account}
                  accountNames={accountNames}
                />
              )}
            </div>
            <div className="col-span-2">
              <PositionsTabs
                holdings={holdings}
                trAccountIds={trAccounts.map((a) => a.id)}
                finizensAccountIds={finizensAccounts.map((a) => a.id)}
                ahorroAccountIds={ahorroAccounts.map((a) => a.id)}
                onAddStock={() => setAddStock(true)}
                onAddFund={() => setAddFund(true)}
                onAddSavings={() => setAddSavings(true)}
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
