import type { LucideIcon } from "lucide-react";
import { AlertTriangle, ArrowDownRight, ArrowUpRight, Database, Inbox, LoaderCircle } from "lucide-react";
import type { ReactNode } from "react";

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description: string;
  actions?: ReactNode;
}) {
  // eyebrow: prop conservada como deprecated para no romper call sites; ya no se renderiza.
  void eyebrow;
  return (
    <header className="flex items-center justify-between gap-6 pb-6">
      <div className="min-w-0">
        <h1 className="text-heading text-[var(--text-primary)]">{title}</h1>
        {description && <p className="mt-1 text-[13px] text-[var(--text-secondary)]">{description}</p>}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </header>
  );
}

export function MetricDelta({ value, positive = true, label }: { value: string; positive?: boolean; label?: string }) {
  const Icon = positive ? ArrowUpRight : ArrowDownRight;
  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium ${positive ? "text-accent-teal" : "text-accent-danger"}`}>
      <Icon size={13} />
      {value}
      {label && <span className="ml-1 font-normal text-stone">{label}</span>}
    </span>
  );
}

export function KpiCard({
  label,
  value,
  hint,
  delta,
  positive = true,
  icon: Icon,
}: {
  label: string;
  value: string;
  hint?: string;
  delta?: string;
  positive?: boolean;
  icon?: LucideIcon;
}) {
  return (
    <article className="premium-card rounded-lg p-5 min-w-0">
      <div className="flex items-center justify-between gap-3">
        <p className="truncate text-xs font-medium text-stone">{label}</p>
        {Icon && (
          <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg border border-hairline-dark bg-[var(--bg-interactive)] text-primary-bright">
            <Icon size={16} />
          </span>
        )}
      </div>
      <p className="financial-number mt-4 truncate text-[22px] leading-none text-on-dark">{value}</p>
      <div className="mt-3 min-h-5">{delta ? <MetricDelta value={delta} positive={positive} label={hint} /> : hint && <p className="text-xs text-mute">{hint}</p>}</div>
    </article>
  );
}

export function ChartCard({
  title,
  description,
  action,
  children,
  className = "",
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section className={`premium-card rounded-lg overflow-hidden ${className}`}>
      <div className="flex items-start justify-between gap-4 border-b border-divider-soft px-5 py-4">
        <div className="min-w-0">
          <h2 className="truncate text-[20px] leading-[1.2] tracking-[-.4px] text-on-dark">{title}</h2>
          {description && <p className="mt-1 text-xs text-stone">{description}</p>}
        </div>
        {action}
      </div>
      <div className="p-5">{children}</div>
    </section>
  );
}

export function EmptyState({
  title,
  description,
  action,
  secondaryAction,
  icon: Icon = Inbox,
  compact = false,
  preview,
}: {
  title: string;
  description: string;
  action?: ReactNode;
  secondaryAction?: ReactNode;
  icon?: LucideIcon;
  compact?: boolean;
  preview?: ReactNode;
}) {
  return (
    <div className={`flex flex-col items-center justify-center text-center ${compact ? "py-8" : "premium-card rounded-lg py-16 px-6"}`}>
      {preview && (
        <div className="relative mb-6 w-full max-w-md opacity-50" style={{ pointerEvents: "none" }} aria-hidden>
          <span className="absolute right-2 top-2 z-10 rounded-full bg-[var(--bg-interactive)] px-2 py-0.5 text-[10px] font-medium text-[var(--text-secondary)]">Ejemplo</span>
          <div className="grayscale">{preview}</div>
        </div>
      )}
      <span className="grid h-11 w-11 place-items-center rounded-lg border border-hairline-dark bg-[var(--bg-interactive)] text-primary-bright">
        <Icon size={20} />
      </span>
      <h3 className="mt-4 text-base font-semibold text-on-dark">{title}</h3>
      <p className="mt-2 max-w-md text-sm leading-6 text-stone">{description}</p>
      {(action || secondaryAction) && <div className="mt-5 flex items-center gap-3">{action}{secondaryAction}</div>}
    </div>
  );
}

export function ErrorState({ title, description, onRetry, action }: { title: string; description: string; onRetry?: () => void; action?: ReactNode }) {
  return (
    <div className="rounded-lg border border-accent-danger/30 bg-accent-danger/5 p-6 flex gap-4">
      <span className="grid h-10 w-10 shrink-0 place-items-center rounded-lg bg-accent-danger/10 text-accent-danger"><AlertTriangle size={19} /></span>
      <div>
        <h3 className="font-semibold text-on-dark">{title}</h3>
        <p className="text-sm text-stone mt-1 max-w-xl">{description}</p>
        <div className="flex gap-3 mt-4">{onRetry && <button onClick={onRetry} className="mercury-button rounded-lg px-4 py-2 text-xs font-semibold">Reintentar</button>}{action}</div>
      </div>
    </div>
  );
}

export function DataSourceBadge({ status = "local", label }: { status?: "live" | "delayed" | "offline" | "error" | "local"; label?: string }) {
  const colors = { live: "text-accent-teal bg-accent-teal/10", delayed: "text-accent-warning bg-accent-warning/10", offline: "text-stone bg-[var(--bg-interactive)]", error: "text-accent-danger bg-accent-danger/10", local: "text-primary-bright bg-primary/10" };
  return <span className={`inline-flex items-center gap-1.5 rounded-lg px-2.5 py-1 text-[11px] font-medium ${colors[status]}`}><Database size={11} />{label ?? ({ live: "Actualizado", delayed: "Dato retrasado", offline: "Offline", error: "Error", local: "Local" }[status])}</span>;
}

export function LoadingState({ label = "Cargando datos" }: { label?: string }) {
  return <div className="flex h-56 flex-col items-center justify-center gap-3 text-sm text-stone"><LoaderCircle className="animate-spin text-primary-bright" /><span>{label}</span></div>;
}
