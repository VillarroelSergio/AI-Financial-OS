import { useState } from "react";
import { PageHeader } from "@/components/ui/Dashboard";
import BudgetTab from "@/features/planning/BudgetTab";
import CashflowTab from "@/features/planning/CashflowTab";
import HouseholdBillsTab from "@/features/planning/HouseholdBillsTab";
import RecurringTab from "@/features/planning/RecurringTab";

type Tab = "presupuestos" | "recurrentes" | "facturas" | "cashflow";

const TABS: { key: Tab; label: string }[] = [
  { key: "presupuestos", label: "Presupuestos" },
  { key: "recurrentes", label: "Recurrentes" },
  { key: "facturas", label: "Facturas hogar" },
  { key: "cashflow", label: "Cashflow" },
];

export default function PlanificacionPage() {
  const tabParam = new URLSearchParams(window.location.search).get("tab");
  const initialTab = TABS.some((tab) => tab.key === tabParam) ? (tabParam as Tab) : "presupuestos";
  const [active, setActive] = useState<Tab>(initialTab);

  return (
    <div className="space-y-6 p-8 max-w-[1500px] mx-auto">
      <PageHeader
        eyebrow="Forecast operativo"
        title="Planificacion"
        description="Presupuestos, recurrentes, facturas del hogar y prevision financiera en una vista accionable."
        actions={<span className="rounded-lg border border-hairline-dark bg-white/[.035] px-3 py-2 text-xs text-stone">Presupuestos - Recurrentes - Facturas - Cashflow</span>}
      />

      <div className="flex gap-1 rounded-lg border border-hairline-dark bg-white/[.035] p-1 w-fit">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActive(tab.key)}
            className={[
              "rounded-lg px-4 py-2 text-sm font-medium transition-colors",
              active === tab.key ? "bg-primary text-white" : "text-stone hover:text-on-dark hover:bg-white/[.04]",
            ].join(" ")}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {active === "presupuestos" && <BudgetTab />}
      {active === "recurrentes" && <RecurringTab />}
      {active === "facturas" && <HouseholdBillsTab />}
      {active === "cashflow" && <CashflowTab />}
    </div>
  );
}
