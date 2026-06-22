import { Route, Routes } from "react-router-dom";
import RootLayout from "@/app/layout/RootLayout";
import AccountsPage from "@/features/accounts/AccountsPage";
import AssistantPage from "@/features/assistant/AssistantPage";
import EconomyPage from "@/features/economy/EconomyPage";
import GoalsPage from "@/features/goals/GoalsPage";
import ImportsPage from "@/features/imports/ImportsPage";
import InsightsPage from "@/features/insights/InsightsPage";
import InvestmentsPage from "@/features/investments/InvestmentsPage";
import MarketsPage from "@/features/markets/MarketsPage";
import OverviewPage from "@/features/overview/OverviewPage";
import SettingsPage from "@/features/settings/SettingsPage";
import SpendingPage from "@/features/spending/SpendingPage";
import TransactionsPage from "@/features/transactions/TransactionsPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<RootLayout />}>
        <Route index element={<OverviewPage />} />
        <Route path="spending" element={<SpendingPage />} />
        <Route path="transactions" element={<TransactionsPage />} />
        <Route path="accounts" element={<AccountsPage />} />
        <Route path="imports" element={<ImportsPage />} />
        <Route path="investments" element={<InvestmentsPage />} />
        <Route path="economy" element={<EconomyPage />} />
        <Route path="markets" element={<MarketsPage />} />
        <Route path="goals" element={<GoalsPage />} />
        <Route path="insights" element={<InsightsPage />} />
        <Route path="assistant" element={<AssistantPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}
