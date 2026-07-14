import { lazy, Suspense, useEffect } from "react";
import { MotionConfig } from "framer-motion";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import RootLayout from "@/app/layout/RootLayout";
import SettingsPage from "@/features/settings/SettingsPage";
import {
  loadAssistantPage,
  loadDashboardPage,
  loadEconomyPage,
  loadFinancesPage,
  loadGoalsPage,
  loadInsightsPage,
  loadInstrumentDetailPage,
  loadInvestmentsPage,
  loadMarketsPage,
  loadPortfolioImportPage,
  loadPositionTrackingPage,
  warmCoreRoutes,
} from "@/app/routes/pageLoaders";

const AssistantPage = lazy(loadAssistantPage);
const DashboardPage = lazy(loadDashboardPage);
const EconomyPage = lazy(loadEconomyPage);
const FinancesPage = lazy(loadFinancesPage);
const GoalsPage = lazy(loadGoalsPage);
const InsightsPage = lazy(loadInsightsPage);
const InvestmentsPage = lazy(loadInvestmentsPage);
const PositionTrackingPage = lazy(loadPositionTrackingPage);
const PortfolioImportPage = lazy(loadPortfolioImportPage);
const MarketsPage = lazy(loadMarketsPage);
const InstrumentDetailPage = lazy(loadInstrumentDetailPage);

type FinancesTab = "cuentas" | "movimientos" | "gastos" | "planificacion" | "importar";

function LegacyFinancesRedirect({ tab }: { tab: FinancesTab }) {
  const { search } = useLocation();
  const source = new URLSearchParams(search);
  const target = new URLSearchParams({ tab });

  source.forEach((value, key) => {
    if (key === "tab" && tab === "planificacion") target.set("planningTab", value);
    else if (key !== "tab") target.set(key, value);
  });

  return <Navigate to={`/finances?${target.toString()}`} replace />;
}

export default function App() {
  useEffect(() => warmCoreRoutes(), []);

  return (
    <MotionConfig reducedMotion="user">
    <Suspense fallback={null}>
    <Routes>
      <Route path="/" element={<RootLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="finances" element={<FinancesPage />} />
        {/* Rutas antiguas → pestañas de Movimientos y cuentas */}
        <Route path="accounts" element={<LegacyFinancesRedirect tab="cuentas" />} />
        <Route path="transactions" element={<LegacyFinancesRedirect tab="movimientos" />} />
        <Route path="spending" element={<LegacyFinancesRedirect tab="gastos" />} />
        <Route path="planificacion" element={<LegacyFinancesRedirect tab="planificacion" />} />
        <Route path="imports" element={<LegacyFinancesRedirect tab="importar" />} />
        <Route path="investments" element={<InvestmentsPage />} />
        <Route path="investments/tracking" element={<PositionTrackingPage />} />
        <Route path="investments/import" element={<PortfolioImportPage />} />
        <Route path="economy" element={<EconomyPage />} />
        <Route path="markets" element={<MarketsPage />} />
        <Route path="markets/:indicatorCode" element={<InstrumentDetailPage />} />
        <Route path="goals" element={<GoalsPage />} />
        <Route path="insights" element={<InsightsPage />} />
        <Route path="assistant" element={<AssistantPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="welcome" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
    </Suspense>
    </MotionConfig>
  );
}
