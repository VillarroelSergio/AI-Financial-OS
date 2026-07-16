import { MotionConfig } from "framer-motion";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import RootLayout from "@/app/layout/RootLayout";
import StartupExperience from "@/app/StartupExperience";
import { ToastProvider } from "@/app/ToastProvider";
import AssistantPage from "@/features/assistant/AssistantPage";
import DashboardPage from "@/features/dashboard/DashboardPage";
import EconomyPage from "@/features/economy/EconomyPage";
import FinancesPage from "@/features/finances/FinancesPage";
import GoalsPage from "@/features/goals/GoalsPage";
import InsightsPage from "@/features/insights/InsightsPage";
import InvestmentsPage from "@/features/investments/InvestmentsPage";
import PositionTrackingPage from "@/features/investments/tracking/PositionTrackingPage";
import PortfolioImportPage from "@/features/investments/import/PortfolioImportPage";
import MarketsPage from "@/features/markets/MarketsPage";
import InstrumentDetailPage from "@/features/markets/detail/InstrumentDetailPage";
import SettingsPage from "@/features/settings/SettingsPage";

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
  return (
    <MotionConfig reducedMotion="user">
      <StartupExperience />
      <ToastProvider>
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
      </ToastProvider>
    </MotionConfig>
  );
}
