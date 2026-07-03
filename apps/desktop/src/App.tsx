import { Route, Routes } from "react-router-dom";
import RootLayout from "@/app/layout/RootLayout";
import AccountsPage from "@/features/accounts/AccountsPage";
import AssistantPage from "@/features/assistant/AssistantPage";
import EconomyPage from "@/features/economy/EconomyPage";
import GoalsPage from "@/features/goals/GoalsPage";
import ImportsPage from "@/features/imports/ImportsPage";
import InsightsPage from "@/features/insights/InsightsPage";
import InvestmentsPage from "@/features/investments/InvestmentsPage";
import PositionTrackingPage from "@/features/investments/tracking/PositionTrackingPage";
import PortfolioImportPage from "@/features/investments/import/PortfolioImportPage";
import MarketsPage from "@/features/markets/MarketsPage";
import OverviewPage from "@/features/overview/OverviewPage";
import SettingsPage from "@/features/settings/SettingsPage";
import PlanificacionPage from "@/pages/PlanificacionPage";
import SpendingPage from "@/features/spending/SpendingPage";
import TransactionsPage from "@/features/transactions/TransactionsPage";
import WelcomeGate from "@/features/welcome/WelcomeGate";
import WelcomePage from "@/features/welcome/WelcomePage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<RootLayout />}>
        <Route index element={<WelcomeGate><OverviewPage /></WelcomeGate>} />
        <Route path="welcome" element={<WelcomePage />} />
        <Route path="spending" element={<SpendingPage />} />
        <Route path="transactions" element={<TransactionsPage />} />
        <Route path="accounts" element={<AccountsPage />} />
        <Route path="imports" element={<ImportsPage />} />
        <Route path="investments" element={<InvestmentsPage />} />
        <Route path="investments/tracking" element={<PositionTrackingPage />} />
        <Route path="investments/import" element={<PortfolioImportPage />} />
        <Route path="economy" element={<EconomyPage />} />
        <Route path="markets" element={<MarketsPage />} />
        <Route path="goals" element={<GoalsPage />} />
        <Route path="planificacion" element={<PlanificacionPage />} />
        <Route path="insights" element={<InsightsPage />} />
        <Route path="assistant" element={<AssistantPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}
