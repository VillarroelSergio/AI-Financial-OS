import { MotionConfig } from "framer-motion";
import { Navigate, Route, Routes } from "react-router-dom";
import RootLayout from "@/app/layout/RootLayout";
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

export default function App() {
  return (
    <MotionConfig reducedMotion="user">
    <Routes>
      <Route path="/" element={<RootLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="finances" element={<FinancesPage />} />
        {/* Rutas antiguas → pestañas de Movimientos y cuentas */}
        <Route path="accounts" element={<Navigate to="/finances?tab=cuentas" replace />} />
        <Route path="transactions" element={<Navigate to="/finances?tab=movimientos" replace />} />
        <Route path="spending" element={<Navigate to="/finances?tab=gastos" replace />} />
        <Route path="planificacion" element={<Navigate to="/finances?tab=planificacion" replace />} />
        <Route path="imports" element={<Navigate to="/finances?tab=importar" replace />} />
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
    </MotionConfig>
  );
}
