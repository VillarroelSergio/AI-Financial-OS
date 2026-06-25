import type { LucideIcon } from "lucide-react";
import { AlertTriangle, ArrowDownRight, ArrowUpRight, Database, Inbox, LoaderCircle } from "lucide-react";
import type { ReactNode } from "react";

export function PageHeader({ eyebrow, title, description, actions }: { eyebrow?: string; title: string; description: string; actions?: ReactNode }) {
  return <header className="flex items-start justify-between gap-6">
    <div>{eyebrow && <p className="text-xs font-medium uppercase tracking-[.18em] text-primary-bright mb-2">{eyebrow}</p>}<h1 className="text-display-lg text-on-dark">{title}</h1><p className="text-body-sm text-stone mt-2">{description}</p></div>
    {actions && <div className="flex items-center gap-3">{actions}</div>}
  </header>;
}

export function MetricDelta({ value, positive = true, label }: { value: string; positive?: boolean; label?: string }) {
  const Icon = positive ? ArrowUpRight : ArrowDownRight;
  return <span className={`inline-flex items-center gap-1 text-xs font-medium ${positive ? "text-accent-teal" : "text-accent-danger"}`}><Icon size={13}/>{value}{label && <span className="font-normal text-stone ml-1">{label}</span>}</span>;
}

export function KpiCard({ label, value, hint, delta, positive = true, icon: Icon }: { label: string; value: string; hint?: string; delta?: string; positive?: boolean; icon?: LucideIcon }) {
  return <article className="premium-card rounded-xl p-5 min-w-0">
    <div className="flex items-center justify-between gap-3"><p className="text-xs font-medium text-stone">{label}</p>{Icon && <span className="grid h-8 w-8 place-items-center rounded-lg bg-primary/10 text-primary-bright"><Icon size={16}/></span>}</div>
    <p className="financial-number mt-4 text-[26px] leading-none font-semibold tracking-[-.03em] text-on-dark">{value}</p>
    <div className="mt-3 min-h-5">{delta ? <MetricDelta value={delta} positive={positive} label={hint}/> : hint && <p className="text-xs text-mute">{hint}</p>}</div>
  </article>;
}

export function ChartCard({ title, description, action, children, className = "" }: { title: string; description?: string; action?: ReactNode; children: ReactNode; className?: string }) {
  return <section className={`premium-card rounded-xl overflow-hidden ${className}`}><div className="flex items-start justify-between gap-4 px-5 pt-5"><div><h2 className="text-base font-semibold text-on-dark">{title}</h2>{description && <p className="text-xs text-stone mt-1">{description}</p>}</div>{action}</div><div className="p-5">{children}</div></section>;
}

export function EmptyState({ title, description, action, secondaryAction, icon: Icon = Inbox, compact = false }: { title: string; description: string; action?: ReactNode; secondaryAction?: ReactNode; icon?: LucideIcon; compact?: boolean }) {
  return <div className={`flex flex-col items-center justify-center text-center ${compact ? "py-8" : "premium-card rounded-xl py-16 px-6"}`}><span className="grid h-11 w-11 place-items-center rounded-xl border border-hairline-dark bg-primary/10 text-primary-bright"><Icon size={20}/></span><h3 className="mt-4 text-base font-semibold text-on-dark">{title}</h3><p className="mt-2 max-w-md text-sm leading-6 text-stone">{description}</p>{(action || secondaryAction) && <div className="mt-5 flex items-center gap-3">{action}{secondaryAction}</div>}</div>;
}

export function ErrorState({ title, description, onRetry, action }: { title: string; description: string; onRetry?: () => void; action?: ReactNode }) {
  return <div className="rounded-xl border border-accent-danger/30 bg-accent-danger/5 p-6 flex gap-4"><span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-accent-danger/10 text-accent-danger"><AlertTriangle size={19}/></span><div><h3 className="font-semibold text-on-dark">{title}</h3><p className="text-sm text-stone mt-1 max-w-xl">{description}</p><div className="flex gap-3 mt-4">{onRetry && <button onClick={onRetry} className="rounded-lg bg-on-dark px-4 py-2 text-xs font-semibold text-black">Reintentar</button>}{action}</div></div></div>;
}

export function DataSourceBadge({ status = "local", label }: { status?: "live" | "delayed" | "offline" | "error" | "local"; label?: string }) {
  const colors = { live: "text-accent-teal bg-accent-teal/10", delayed: "text-amber-300 bg-amber-400/10", offline: "text-stone bg-white/5", error: "text-accent-danger bg-accent-danger/10", local: "text-sky-300 bg-sky-400/10" };
  return <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[11px] font-medium ${colors[status]}`}><Database size={11}/>{label ?? ({live:"Actualizado", delayed:"Dato retrasado", offline:"Offline", error:"Error", local:"Local"}[status])}</span>;
}

export function LoadingState({ label = "Cargando datos" }: { label?: string }) {
  return <div className="flex h-56 flex-col items-center justify-center gap-3 text-sm text-stone"><LoaderCircle className="animate-spin text-primary-bright"/><span>{label}</span></div>;
}
