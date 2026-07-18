import { useSearchParams } from "react-router-dom";
import AccountsPage from "@/features/accounts/AccountsPage";
import ImportsPage from "@/features/imports/ImportsPage";
import SpendingPage from "@/features/spending/SpendingPage";
import TransactionsPage from "@/features/transactions/TransactionsPage";
import PlanificacionPage from "@/pages/PlanificacionPage";

const TABS = [
  { id: "cuentas", label: "Cuentas" },
  { id: "movimientos", label: "Movimientos" },
  { id: "gastos", label: "Gastos" },
  { id: "planificacion", label: "Planificación" },
  { id: "importar", label: "Importar" },
] as const;

type TabId = (typeof TABS)[number]["id"];

export default function FinancesPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const raw = searchParams.get("tab");
  const tab: TabId = TABS.some((t) => t.id === raw) ? (raw as TabId) : "cuentas";

  return (
    <div className="flex min-h-full flex-col">
      <div
        className="sticky top-0 z-10"
        style={{ background: "var(--bg-app)" }}
      >
        <div className="page-tabs flex gap-1 py-3">
          {TABS.map(({ id, label }) => (
            <button
              key={id}
              onClick={() => setSearchParams({ tab: id })}
              className={`border-b-2 px-4 py-2.5 text-sm transition-colors ${
                tab === id
                  ? "border-[var(--primary)] text-[var(--text-primary)]"
                  : "border-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
      </div>
      {tab === "cuentas" && <AccountsPage />}
      {tab === "movimientos" && <TransactionsPage />}
      {tab === "gastos" && <SpendingPage />}
      {tab === "planificacion" && <PlanificacionPage />}
      {tab === "importar" && <ImportsPage />}
    </div>
  );
}
