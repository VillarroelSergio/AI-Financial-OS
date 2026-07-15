import { useSearchParams } from "react-router-dom";
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
  const [searchParams, setSearchParams] = useSearchParams();
  const tabParam = searchParams.get("planningTab");
  const active: Tab = TABS.some((tab) => tab.key === tabParam) ? (tabParam as Tab) : "presupuestos";

  const selectTab = (nextTab: Tab) => {
    const next = new URLSearchParams(searchParams);
    next.set("tab", "planificacion");
    next.set("planningTab", nextTab);
    setSearchParams(next);
  };

  return (
    <div className="page-shell space-y-6">
      <PageHeader
        eyebrow="Forecast operativo"
        title="Planificación"
        description="Presupuestos, recurrentes, facturas del hogar y prevision financiera en una vista accionable."
      />

      <SegmentedControl options={TABS} value={active} onChange={selectTab} ariaLabel="Secciones de planificación" />

      {active === "presupuestos" && <BudgetTab />}
      {active === "recurrentes" && <RecurringTab />}
      {active === "facturas" && <HouseholdBillsTab />}
      {active === "cashflow" && <CashflowTab />}
    </div>
  );
}
