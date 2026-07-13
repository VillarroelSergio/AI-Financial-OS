import { useState } from "react";
import { PageHeader } from "@/components/ui/Dashboard";
import SegmentedControl from "@/components/ui/SegmentedControl";
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
        title="Planificación"
        description="Presupuestos, recurrentes, facturas del hogar y prevision financiera en una vista accionable."
      />

      <SegmentedControl options={TABS} value={active} onChange={setActive} ariaLabel="Secciones de planificación" />

      {active === "presupuestos" && <BudgetTab />}
      {active === "recurrentes" && <RecurringTab />}
      {active === "facturas" && <HouseholdBillsTab />}
      {active === "cashflow" && <CashflowTab />}
    </div>
  );
}
