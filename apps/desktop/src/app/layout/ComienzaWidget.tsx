import { useState } from "react";
import { ArrowRight, Check, ChevronDown, ChevronUp, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAccounts } from "@/lib/hooks/useAccounts";
import { useHoldings } from "@/lib/hooks/useInvestments";
import { useSpendingYears } from "@/lib/hooks/useDashboard";

const DISMISS_KEY = "comienza-dismissed";

export default function ComienzaWidget() {
  const navigate = useNavigate();
  const [dismissed, setDismissed] = useState(() => localStorage.getItem(DISMISS_KEY) === "true");
  const [expanded, setExpanded] = useState(false);
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
  const compact = doneCount >= 2 && !expanded;

  if (dismissed || doneCount === steps.length) return null;

  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, "true");
    setDismissed(true);
  };

  return (
    <div className="mt-4 rounded-xl border border-[var(--border-soft)] bg-[var(--bg-card)] p-3.5">
      <div className="flex items-center justify-between">
        <p className="font-semibold text-[var(--color-frost-white)]" style={{ fontSize: "13px" }}>Comienza</p>
        <div className="flex items-center gap-2">
          <span
            className="grid h-6 w-6 place-items-center rounded-full"
            style={{ background: `conic-gradient(var(--primary) ${(doneCount / steps.length) * 360}deg, rgba(255,255,255,0.1) 0deg)` }}
          >
            <span className="h-4 w-4 rounded-full bg-[var(--bg-card)]" />
          </span>
          <button onClick={dismiss} aria-label="Cerrar guia" className="text-[var(--color-platinum)] hover:text-[var(--color-frost-white)]">
            <X size={13} />
          </button>
        </div>
      </div>
      <p className="mt-1 text-[var(--color-platinum)]" style={{ fontSize: "11px" }}>{doneCount}/{steps.length} completados</p>
      {compact && (
        <button onClick={() => setExpanded(true)} className="mt-2 flex w-full items-center justify-between rounded-lg bg-white/[.035] px-2.5 py-2 text-left text-[var(--color-platinum)] hover:text-[var(--color-frost-white)]" style={{ fontSize: "11px" }}>
          <span>Ver el paso pendiente</span><ChevronDown size={13} />
        </button>
      )}
      {!compact && <div className="mt-2 space-y-1">
        {steps.map((step) => (
          <div key={step.label} className="flex items-start gap-2 border-t border-[rgba(255,255,255,0.05)] pt-1.5">
            <span className={`mt-0.5 grid h-3.5 w-3.5 shrink-0 place-items-center rounded ${step.done ? "bg-emerald-500 text-emerald-950" : "border border-[var(--border-soft)]"}`}>
              {step.done && <Check size={9} />}
            </span>
            <div className="min-w-0">
              <p className={step.done ? "text-[var(--color-platinum)] line-through" : "text-[var(--color-frost-white)]"} style={{ fontSize: "11.5px" }}>
                {step.label}
              </p>
              {!step.done && (
                <button onClick={() => navigate(step.to)} className="flex items-center gap-1 text-[var(--primary)] hover:underline" style={{ fontSize: "11px" }}>
                  Ir <ArrowRight size={10} />
                </button>
              )}
            </div>
          </div>
        ))}
        {doneCount >= 2 && <button onClick={() => setExpanded(false)} className="flex w-full items-center justify-end gap-1 pt-1 text-[var(--color-platinum)] hover:text-[var(--color-frost-white)]" style={{ fontSize: "11px" }}>Minimizar <ChevronUp size={12} /></button>}
      </div>
      }
    </div>
  );
}
