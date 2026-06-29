import { useState } from "react";
import BudgetTab from "@/features/planning/BudgetTab";
import CashflowTab from "@/features/planning/CashflowTab";
import RecurringTab from "@/features/planning/RecurringTab";

type Tab = "presupuestos" | "recurrentes" | "cashflow";

const TABS: { key: Tab; label: string }[] = [
  { key: "presupuestos", label: "Presupuestos" },
  { key: "recurrentes", label: "Recurrentes" },
  { key: "cashflow", label: "Cashflow" },
];

export default function PlanificacionPage() {
  const [active, setActive] = useState<Tab>("presupuestos");

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold text-on-dark">Planificación</h1>
        <p className="text-sm text-stone">Presupuestos, gastos recurrentes y previsión financiera</p>
      </div>

      <div className="flex gap-1 rounded-xl bg-surface-elevated p-1 w-fit">
        {TABS.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActive(tab.key)}
            className={[
              "rounded-lg px-4 py-2 text-sm font-medium transition-colors",
              active === tab.key ? "bg-primary text-white" : "text-stone hover:text-on-dark",
            ].join(" ")}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {active === "presupuestos" && <BudgetTab />}
      {active === "recurrentes" && <RecurringTab />}
      {active === "cashflow" && <CashflowTab />}
    </div>
  );
}
