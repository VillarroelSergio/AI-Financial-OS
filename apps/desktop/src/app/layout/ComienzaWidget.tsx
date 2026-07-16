import { useState } from "react";
import { ArrowRight, Check, ChevronDown, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAccounts } from "@/lib/hooks/useAccounts";
import { useHoldings } from "@/lib/hooks/useInvestments";
import { useSpendingYears } from "@/lib/hooks/useDashboard";

const DISMISS_KEY = "comienza-dismissed";

export default function ComienzaWidget() {
  const navigate = useNavigate();
  const [dismissed, setDismissed] = useState(() => localStorage.getItem(DISMISS_KEY) === "true");
  const [open, setOpen] = useState(false);
  const { accounts } = useAccounts();
  const { holdings } = useHoldings();
  const years = useSpendingYears();

  const steps = [
    { label: "Crea tu cuenta bancaria", done: accounts.length > 0, to: "/finances?tab=cuentas" },
    { label: "Importa movimientos", done: years.length > 0, to: "/finances?tab=importar" },
    { label: "Da de alta tus acciones", done: holdings.some((h) => h.asset_type === "stock" || h.asset_type === "etf"), to: "/investments" },
    { label: "Añade fondos y ahorro", done: holdings.some((h) => ["fund", "savings_account", "cash"].includes(h.asset_type)), to: "/investments" },
  ];
  const doneCount = steps.filter((s) => s.done).length;

  // Cuando está 4/4 el widget desaparece definitivamente.
  if (dismissed || doneCount === steps.length) return null;

  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, "true");
    setDismissed(true);
  };

  return (
    <div className="mt-4">
      {/* Píldora compacta */}
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-controls="comienza-checklist"
        className="flex w-full items-center gap-2.5 rounded-[10px] border border-[var(--border-soft)] bg-[var(--bg-card)] px-3 py-2 text-left transition-colors hover:bg-[var(--bg-interactive)]"
      >
        <span
          className="grid h-6 w-6 shrink-0 place-items-center rounded-full"
          style={{ background: `conic-gradient(var(--primary) ${(doneCount / steps.length) * 360}deg, var(--border-soft) 0deg)` }}
        >
          <span className="grid h-4 w-4 place-items-center rounded-full bg-[var(--bg-card)] text-[9px] font-semibold text-[var(--text-secondary)]">
            {doneCount}
          </span>
        </span>
        <span className="min-w-0 flex-1">
          <span className="block font-semibold text-[var(--text-primary)]" style={{ fontSize: "13px" }}>Comienza</span>
          <span className="block text-[var(--text-secondary)]" style={{ fontSize: "11px" }}>{doneCount}/{steps.length} completados</span>
        </span>
        <ChevronDown size={14} className={`shrink-0 text-[var(--text-secondary)] transition-transform ${open ? "rotate-180" : ""}`} />
      </button>

      {/* Checklist desplegable */}
      {open && (
        <div id="comienza-checklist" className="motion-popover mt-1.5 rounded-[10px] border border-[var(--border-soft)] bg-[var(--bg-card)] p-3">
          <div className="mb-2 flex items-center justify-end">
            <button onClick={dismiss} aria-label="Cerrar guía" className="grid h-6 w-6 place-items-center rounded text-[var(--text-secondary)] hover:bg-[var(--bg-interactive)] hover:text-[var(--text-primary)]">
              <X size={13} />
            </button>
          </div>
          <div className="space-y-1">
            {steps.map((step) => (
              <div key={step.label} className="flex items-start gap-2 border-t border-[var(--divider-soft)] pt-1.5 first:border-t-0 first:pt-0">
                <span className={`mt-0.5 grid h-3.5 w-3.5 shrink-0 place-items-center rounded ${step.done ? "bg-[var(--positive)] text-white" : "border border-[var(--border-soft)]"}`}>
                  {step.done && <Check size={9} />}
                </span>
                <div className="min-w-0">
                  <p className={step.done ? "text-[var(--text-secondary)] line-through" : "text-[var(--text-primary)]"} style={{ fontSize: "11.5px" }}>
                    {step.label}
                  </p>
                  {!step.done && (
                    <button onClick={() => navigate(step.to)} className="flex min-h-[24px] items-center gap-1 text-[var(--primary)] hover:underline" style={{ fontSize: "11px" }}>
                      Ir <ArrowRight size={10} />
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
