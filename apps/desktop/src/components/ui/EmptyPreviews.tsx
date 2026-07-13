import { Sparkles } from "lucide-react";

/** Mini-maquetas ilustrativas ("Ejemplo") para los EmptyState. Solo CSS/tokens, sin datos reales ni gráficos montados. */

function Bar({ label, pct, value }: { label: string; pct: number; value: string }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-[11px] text-[var(--text-secondary)]">
        <span>{label}</span>
        <span className="financial-number text-[var(--text-primary)]">{value}</span>
      </div>
      <div className="h-2 rounded-full bg-[var(--bg-interactive)]">
        <div className="h-2 rounded-full bg-[var(--primary)]" style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function Card({ children }: { children: React.ReactNode }) {
  return <div className="rounded-lg border border-[var(--border-soft)] bg-[var(--bg-card)] p-4 shadow-[var(--shadow-card)]">{children}</div>;
}

export function BudgetPreview() {
  return (
    <Card>
      <div className="space-y-3">
        <Bar label="Alimentación" pct={64} value="320 / 500 €" />
        <Bar label="Transporte" pct={45} value="90 / 200 €" />
        <Bar label="Ocio" pct={88} value="176 / 200 €" />
      </div>
    </Card>
  );
}

export function InsightsPreview() {
  return (
    <Card>
      <div className="flex items-start gap-3">
        <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-[var(--primary)]/10 text-[var(--primary)]"><Sparkles size={16} /></span>
        <div className="space-y-1.5">
          <p className="text-[13px] text-[var(--text-primary)]">Gastaste <b>un 18% menos</b> en restaurantes este mes.</p>
          <p className="text-[11px] text-[var(--text-secondary)]">Ver desglose →</p>
        </div>
      </div>
    </Card>
  );
}

export function InvestmentsPreview() {
  const rows = [
    { name: "MSCI World ETF", value: "12.400 €", ret: "+8,2%" },
    { name: "Bono estatal", value: "5.000 €", ret: "+2,1%" },
  ];
  return (
    <Card>
      <div className="space-y-2">
        {rows.map((r) => (
          <div key={r.name} className="flex items-center justify-between border-b border-[var(--divider-soft)] pb-2 text-[12px] last:border-0 last:pb-0">
            <span className="text-[var(--text-primary)]">{r.name}</span>
            <span className="flex items-center gap-3">
              <span className="financial-number text-[var(--text-primary)]">{r.value}</span>
              <span className="text-[var(--positive)]">{r.ret}</span>
            </span>
          </div>
        ))}
      </div>
    </Card>
  );
}
