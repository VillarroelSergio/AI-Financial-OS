import { useState } from "react";
import { Plus, RefreshCw } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { EmptyState, PageHeader } from "@/components/ui/Dashboard";
import SegmentedControl from "@/components/ui/SegmentedControl";
import { InvestmentsPreview } from "@/components/ui/EmptyPreviews";
import MetricCard from "@/components/ui/MetricCard";
import Spinner from "@/components/ui/Spinner";
import { useAccounts } from "@/lib/hooks/useAccounts";
import { useHoldings, useInvestmentSummary, useRefreshPrices } from "@/lib/hooks/useInvestments";
import { mergeHoldings, deleteSavings } from "@/lib/api/investments";
import { formatCurrency } from "@/lib/formatters/currency";
import DistributionChart from "./components/DistributionChart";
import PortfolioByTypeCards from "./components/PortfolioByTypeCards";
import PortfolioEvolutionChart from "./components/PortfolioEvolutionChart";
import PositionsTable from "./components/PositionsTable";
import SavingsSummaryPanel from "./components/SavingsSummaryPanel";
import ManualNavDialog from "./components/ManualNavDialog";
import AddStockDialog from "./components/AddStockDialog";
import AddFundDialog from "./components/AddFundDialog";
import AddSavingsDialog from "./components/AddSavingsDialog";
import HoldingEditor from "./components/HoldingEditor";
import HoldingHistoryDialog from "./components/HoldingHistoryDialog";
import FundValuationDialog from "./components/FundValuationDialog";
import SavingsDetailDialog from "./components/SavingsDetailDialog";
import SavingsEditDialog from "./components/SavingsEditDialog";
import ReconciliationTab from "@/features/investments/reconciliation/ReconciliationTab";
import type { HoldingEnriched } from "@/lib/types";

export default function InvestmentsPage() {
  const searchParams = new URLSearchParams(window.location.search);
  const demoEmpty = searchParams.get("demo") === "empty";
  const initialTab = searchParams.get("tab") === "quality" ? "reconciliacion" : "posiciones";
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
  const [historyHolding, setHistoryHolding] = useState<HoldingEnriched | null>(null);
  const [fundHolding, setFundHolding] = useState<HoldingEnriched | null>(null);
  const [savingsHolding, setSavingsHolding] = useState<HoldingEnriched | null>(null);
  const [savingsEditHolding, setSavingsEditHolding] = useState<HoldingEnriched | null>(null);
  const [activeTab, setActiveTab] = useState<"posiciones" | "reconciliacion">(initialTab);

  const navigate = useNavigate();
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
    // Las cuentas remuneradas editan su configuración (tipo/TAE), no el holding genérico.
    if (holding.asset.asset_type === "savings_account") {
      setSavingsEditHolding(holding);
      return;
    }
    setEditingHolding(holding);
    setEditorOpen(true);
  };
  const deleteHolding = async (holding: HoldingEnriched) => {
    // Al borrar una cuenta remunerada hay que borrar también su config, si no la cuenta
    // queda "ya configurada" y no se puede volver a dar de alta (409).
    if (holding.asset.asset_type === "savings_account") {
      await deleteSavings(holding.account_id).catch(() => {});
    }
    await remove(holding.id);
    onRefreshAll();
  };

  // Duplicados: mismo activo (ticker o nombre) en la misma cuenta. Se fusiona el de
  // menor valor dentro del mayor para conservar la posición principal (BUG-INV-1).
  const dupGroups = Object.values(
    holdings.reduce<Record<string, HoldingEnriched[]>>((acc, h) => {
      const key = `${h.account_id}::${(h.symbol || h.display_name || "").toLowerCase()}`;
      (acc[key] ||= []).push(h);
      return acc;
    }, {}),
  ).filter((g) => g.length > 1);

  const mergeGroup = async (group: HoldingEnriched[]) => {
    const byValue = [...group].sort(
      (a, b) => Number(b.market_value ?? 0) - Number(a.market_value ?? 0),
    );
    const target = byValue[0];
    for (const src of byValue.slice(1)) {
      await mergeHoldings(src.id, target.id);
    }
    onRefreshAll();
  };

  // Fusionar desde el menú de una fila: fusiona todo su grupo de duplicados.
  const mergeableIds = new Set(dupGroups.flatMap((g) => g.map((h) => h.id)));
  const mergeHolding = (holding: HoldingEnriched) => {
    const group = dupGroups.find((g) => g.some((h) => h.id === holding.id));
    if (group) mergeGroup(group);
  };

  return (
    <div className="page-shell space-y-xl">
      <PageHeader
        eyebrow="Portfolio desk"
        title="Inversiones"
        description={lastUpdated ? `Ultima actualizacion: ${lastUpdated}` : "Control de posiciones, precios, calidad y cobertura de cartera."}
        actions={
          <>
          <button onClick={openAdd} className="mercury-button-primary flex items-center gap-sm px-md py-sm rounded-lg text-body-sm transition-colors">
            <Plus size={14} />
            Anadir
          </button>
          <button
            onClick={triggerRefresh}
            disabled={refreshing}
            className="mercury-button flex items-center gap-sm px-md py-sm rounded-lg text-body-sm disabled:opacity-50"
          >
            <RefreshCw size={14} className={refreshing ? "animate-spin" : ""} />
            {refreshing ? "Actualizando" : "Precios"}
          </button>
          <button
            onClick={() => navigate("/investments/import")}
            className="mercury-button flex items-center gap-sm px-md py-sm rounded-lg text-body-sm"
          >
            Importar
          </button>
          <button
            onClick={() => navigate("/investments/tracking")}
            className="mercury-button flex items-center gap-sm px-md py-sm rounded-lg text-body-sm"
          >
            Seguimiento
          </button>
          </>
        }
      />

      {editorOpen && (
        <HoldingEditor
          holding={editingHolding}
          accounts={accounts}
          onClose={() => setEditorOpen(false)}
          onSaved={onRefreshAll}
        />
      )}

      {refreshResult && (
        <div className="premium-card rounded-lg p-lg">
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
              <button onClick={clearResult} className="mercury-button rounded-lg px-md py-xs text-caption">
                Cerrar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main tabs */}
      <SegmentedControl
        ariaLabel="Vista de inversiones"
        value={activeTab}
        onChange={setActiveTab}
        options={[
          { key: "posiciones", label: "Posiciones" },
          { key: "reconciliacion", label: "Calidad de cartera" },
        ]}
      />

      {!hasHoldings && activeTab === "posiciones" ? (
        <EmptyState
          title="Sin posiciones"
          description="Añade tus primeras inversiones para ver el estado de tu cartera."
          preview={<InvestmentsPreview />}
          action={
            <button
              onClick={openAdd}
              className="px-lg py-sm rounded-md text-body-sm bg-primary text-on-primary hover:bg-primary/90 transition-colors"
            >
              Anadir activo
            </button>
          }
          secondaryAction={
            <button
              onClick={() => setAddSavings(true)}
              className="mercury-button px-lg py-sm rounded-md text-body-sm"
            >
              + Cuenta de ahorro
            </button>
          }
        />
      ) : activeTab === "posiciones" ? (
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

          {summary && summary.pending_valuation_count > 0 && (
            <p className="text-caption text-mute -mt-md">
              {summary.pending_valuation_count} posición(es) sin valorar ({formatCurrency(summary.pending_valuation_invested)} aportado) no se incluyen en la rentabilidad hasta que tengan valor.
            </p>
          )}

          <PortfolioByTypeCards holdings={realHoldings} />

          <PortfolioEvolutionChart />

          {dupGroups.length > 0 && (
            <div className="premium-card rounded-lg p-lg flex items-center justify-between gap-md">
              <p className="text-caption text-stone">
                Se detectaron {dupGroups.length} posición(es) duplicada(s). Fusiónalas para no contar el coste dos veces.
              </p>
              <div className="flex shrink-0 gap-sm">
                {dupGroups.map((g, i) => (
                  <button
                    key={i}
                    onClick={() => mergeGroup(g)}
                    className="mercury-button rounded-lg px-md py-xs text-caption"
                  >
                    Fusionar {g[0].symbol || g[0].display_name}
                  </button>
                ))}
              </div>
            </div>
          )}

          <DistributionChart holdings={realHoldings} accountNames={accountNames} />

          <PositionsTable
            holdings={realHoldings.filter((h) => h.asset.asset_type !== "savings_account")}
            accountNames={accountNames}
            mergeableIds={mergeableIds}
            onAddStock={openAdd}
            onAddFund={() => setAddFund(true)}
            onEdit={openEdit}
            onDelete={deleteHolding}
            onMerge={mergeHolding}
            onHistory={setHistoryHolding}
            onFundValue={setFundHolding}
          />

          <SavingsSummaryPanel
            holdings={realHoldings.filter((h) => h.asset.asset_type === "savings_account")}
            onAddSavings={() => setAddSavings(true)}
            onEdit={openEdit}
            onDelete={deleteHolding}
            onDetail={setSavingsHolding}
          />
        </>
      ) : (
        <ReconciliationTab />
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
        accounts={accounts}
        onClose={() => setAddFund(false)}
        onSuccess={onRefreshAll}
      />
      <AddSavingsDialog
        open={addSavings}
        accountId={ahorroId}
        onClose={() => setAddSavings(false)}
        onSuccess={onRefreshAll}
      />
      <HoldingHistoryDialog
        holding={historyHolding}
        onClose={() => setHistoryHolding(null)}
        onChanged={onRefreshAll}
      />
      <FundValuationDialog
        holding={fundHolding}
        onClose={() => setFundHolding(null)}
        onChanged={onRefreshAll}
      />
      <SavingsDetailDialog
        holding={savingsHolding}
        onClose={() => setSavingsHolding(null)}
      />
      <SavingsEditDialog
        holding={savingsEditHolding}
        onClose={() => setSavingsEditHolding(null)}
        onSaved={onRefreshAll}
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
