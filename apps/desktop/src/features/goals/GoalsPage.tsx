import { useState } from "react";
import { CalendarDays, Plus, Target, Trash2, TrendingUp } from "lucide-react";
import { EmptyState, ErrorState, LoadingState, PageHeader } from "@/components/ui/Dashboard";
import { formatCurrency } from "@/lib/formatters/currency";
import { useGoals } from "@/lib/hooks/useGoals";
import type { GoalCreate } from "@/lib/api/goals";
import GoalSimulationPanel from "./components/GoalSimulationPanel";

const EMPTY: GoalCreate = {
  name: "",
  type: "custom",
  target_amount: "",
  current_amount: "0",
  target_date: null,
  monthly_contribution: null,
  priority: "medium",
};

const TYPE_LABELS: Record<string, string> = {
  emergency_fund: "Fondo de emergencia",
  housing: "Vivienda",
  investment: "Inversión",
  savings: "Ahorro",
  custom: "Personalizado",
};

const PRIORITY_LABELS: Record<string, string> = {
  low: "Prioridad baja",
  medium: "Prioridad media",
  high: "Prioridad alta",
};

const PRIORITY_COLORS: Record<string, string> = {
  low: "text-stone",
  medium: "text-primary-bright",
  high: "text-amber-400",
};

export default function GoalsPage() {
  const { goals, loading, error, reload, add, remove } = useGoals();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<GoalCreate>(EMPTY);
  const [saving, setSaving] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSaving(true);
    setActionError(null);
    try {
      await add(form);
      setForm(EMPTY);
      setOpen(false);
    } catch {
      setActionError("No se ha podido crear el objetivo. Revisa los importes e inténtalo de nuevo.");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingState label="Cargando objetivos" />;

  return (
    <div className="p-8 max-w-[1500px] mx-auto space-y-6">
      <PageHeader
        eyebrow="Planificación"
        title="Objetivos"
        description="Convierte tus prioridades financieras en un plan medible con proyecciones de escenarios"
        actions={
          <button
            onClick={() => setOpen(true)}
            className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold"
          >
            <Plus size={16} />
            Crear objetivo
          </button>
        }
      />

      {error && (
        <ErrorState
          title="No se han podido cargar los objetivos"
          description={error}
          onRetry={reload}
        />
      )}
      {actionError && (
        <ErrorState
          title="No se ha podido completar la acción"
          description={actionError}
        />
      )}

      {/* Create form */}
      {open && (
        <form
          onSubmit={submit}
          className="premium-card rounded-xl p-6 space-y-5"
        >
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Nuevo objetivo</h2>
            <button
              type="button"
              onClick={() => setOpen(false)}
              className="text-sm text-stone"
            >
              Cancelar
            </button>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <label className="col-span-2 text-sm text-stone">
              Nombre
              <input
                required
                maxLength={120}
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="mt-2 w-full rounded-lg border border-hairline-dark bg-surface-elevated px-3 py-2.5 text-on-dark"
                placeholder="Fondo de emergencia"
              />
            </label>
            <label className="text-sm text-stone">
              Tipo
              <select
                value={form.type}
                onChange={(e) => setForm({ ...form, type: e.target.value as GoalCreate["type"] })}
                className="mt-2 w-full rounded-lg border border-hairline-dark bg-surface-elevated px-3 py-2.5 text-on-dark"
              >
                {Object.entries(TYPE_LABELS).map(([v, l]) => (
                  <option key={v} value={v}>{l}</option>
                ))}
              </select>
            </label>
            <label className="text-sm text-stone">
              Prioridad
              <select
                value={form.priority}
                onChange={(e) => setForm({ ...form, priority: e.target.value as GoalCreate["priority"] })}
                className="mt-2 w-full rounded-lg border border-hairline-dark bg-surface-elevated px-3 py-2.5 text-on-dark"
              >
                <option value="low">Baja</option>
                <option value="medium">Media</option>
                <option value="high">Alta</option>
              </select>
            </label>
            <label className="text-sm text-stone">
              Cantidad objetivo (€)
              <input
                required
                min="0.01"
                step="0.01"
                type="number"
                value={form.target_amount}
                onChange={(e) => setForm({ ...form, target_amount: e.target.value })}
                className="mt-2 w-full rounded-lg border border-hairline-dark bg-surface-elevated px-3 py-2.5 text-on-dark"
              />
            </label>
            <label className="text-sm text-stone">
              Ahorrado actualmente (€)
              <input
                min="0"
                step="0.01"
                type="number"
                value={form.current_amount}
                onChange={(e) => setForm({ ...form, current_amount: e.target.value })}
                className="mt-2 w-full rounded-lg border border-hairline-dark bg-surface-elevated px-3 py-2.5 text-on-dark"
              />
            </label>
            <label className="text-sm text-stone">
              Aportación mensual (€)
              <input
                min="0"
                step="0.01"
                type="number"
                value={form.monthly_contribution ?? ""}
                onChange={(e) =>
                  setForm({ ...form, monthly_contribution: e.target.value || null })
                }
                className="mt-2 w-full rounded-lg border border-hairline-dark bg-surface-elevated px-3 py-2.5 text-on-dark"
                placeholder="Opcional"
              />
            </label>
            <label className="text-sm text-stone">
              Fecha objetivo
              <input
                type="date"
                value={form.target_date ?? ""}
                onChange={(e) =>
                  setForm({ ...form, target_date: e.target.value || null })
                }
                className="mt-2 w-full rounded-lg border border-hairline-dark bg-surface-elevated px-3 py-2.5 text-on-dark"
              />
            </label>
          </div>
          <button
            disabled={saving}
            className="rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold disabled:opacity-50"
          >
            {saving ? "Guardando…" : "Guardar objetivo"}
          </button>
        </form>
      )}

      {/* Empty state */}
      {!error && goals.length === 0 ? (
        <EmptyState
          icon={Target}
          title="Define tus próximos objetivos financieros"
          description="Crea metas como fondo de emergencia, entrada de vivienda o inversión a largo plazo. Verás proyecciones con tres escenarios de crecimiento."
          preview={
            <div className="space-y-3 rounded-2xl border border-[var(--border-soft)] bg-[var(--bg-card)] p-4 text-left">
              {[
                { name: "Fondo de emergencia", pct: 72 },
                { name: "Entrada de vivienda", pct: 34 },
              ].map((g) => (
                <div key={g.name}>
                  <div className="mb-1 flex justify-between text-[11px] text-[var(--text-secondary)]">
                    <span>{g.name}</span>
                    <span>{g.pct}%</span>
                  </div>
                  <div className="h-2 rounded-full bg-[var(--bg-interactive)]">
                    <div className="h-2 rounded-full bg-[var(--primary)]" style={{ width: `${g.pct}%` }} />
                  </div>
                </div>
              ))}
            </div>
          }
          action={
            <button
              onClick={() => setOpen(true)}
              className="inline-flex items-center gap-2 rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold"
            >
              <Plus size={16} />
              Crear objetivo
            </button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
          {goals.map((goal) => {
            const progress = Math.min(
              100,
              (Number(goal.current_amount) / Math.max(1, Number(goal.target_amount))) * 100
            );
            const hasContribution =
              goal.monthly_contribution !== null && parseFloat(goal.monthly_contribution) > 0;

            return (
              <article key={goal.id} className="premium-card rounded-xl overflow-hidden">
                <div className="p-5">
                  {/* Header */}
                  <div className="flex justify-between gap-4">
                    <div>
                      <p className={`text-xs uppercase tracking-wider ${PRIORITY_COLORS[goal.priority]}`}>
                        {TYPE_LABELS[goal.type] ?? goal.type}
                        {" · "}
                        {PRIORITY_LABELS[goal.priority]}
                      </p>
                      <h2 className="mt-1.5 text-lg font-semibold text-on-dark">{goal.name}</h2>
                    </div>
                    <button
                      aria-label={`Eliminar ${goal.name}`}
                      onClick={() =>
                        void remove(goal.id).catch(() =>
                          setActionError("No se ha podido eliminar el objetivo.")
                        )
                      }
                      className="h-9 w-9 grid place-items-center rounded-lg text-stone hover:bg-accent-danger/10 hover:text-accent-danger shrink-0"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>

                  {/* Progress */}
                  <div className="mt-5 flex justify-between financial-number text-sm">
                    <span className="text-on-dark font-semibold">
                      {formatCurrency(goal.current_amount)}
                    </span>
                    <span className="text-stone">
                      de {formatCurrency(goal.target_amount)}
                    </span>
                  </div>
                  <div className="mt-2 h-2 overflow-hidden rounded-full bg-[var(--bg-interactive)]">
                    <div
                      className="h-full rounded-full bg-primary transition-all duration-500"
                      style={{ width: `${progress}%` }}
                    />
                  </div>

                  {/* Meta row */}
                  <div className="mt-3 flex justify-between text-xs text-stone">
                    <span>{progress.toFixed(0)} % completado</span>
                    <div className="flex items-center gap-3">
                      {hasContribution && (
                        <span className="flex items-center gap-1 text-emerald-400/70">
                          <TrendingUp size={11} />
                          +{formatCurrency(goal.monthly_contribution!)}/mes
                        </span>
                      )}
                      {goal.target_date && (
                        <span className="flex items-center gap-1">
                          <CalendarDays size={11} />
                          {new Date(`${goal.target_date}T00:00:00`).toLocaleDateString("es-ES", {
                            day: "2-digit",
                            month: "short",
                            year: "numeric",
                          })}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                {/* Simulation panel */}
                <GoalSimulationPanel
                  goalId={goal.id}
                  targetAmount={goal.target_amount}
                  hasContribution={hasContribution}
                />
              </article>
            );
          })}
        </div>
      )}
    </div>
  );
}
