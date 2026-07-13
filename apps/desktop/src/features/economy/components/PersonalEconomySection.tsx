import { useMemo, useState } from "react";
import { Home, Landmark, Newspaper, PiggyBank, TrendingDown, TrendingUp, Wallet } from "lucide-react";
import { formatCurrency } from "@/lib/formatters/currency";
import type { MacroDataPointMI, PersonalEconomyMI } from "@/lib/types/market-intelligence";

const pct = (v: number | null | undefined, decimals = 1) =>
  v === null || v === undefined ? "—" : `${v.toFixed(decimals)}%`;

// ── Semáforo de contexto España (Fase 2) ─────────────────────────────
function contextItems(spain: MacroDataPointMI[]) {
  const byId = new Map(spain.map((i) => [i.catalog_item_id, i]));
  const items: { id: string; tone: "good" | "bad" | "flat"; text: string }[] = [];
  const push = (id: string, tone: "good" | "bad" | "flat", text: string) => items.push({ id, tone, text });

  const paro = byId.get("desempleo_spain");
  if (paro?.value != null) {
    const delta = paro.delta ?? 0;
    const trend = delta < 0 ? "y baja" : delta > 0 ? "y sube" : "estable";
    push("paro", delta < 0 ? "good" : delta > 0 ? "bad" : "flat", `Paro en ${pct(paro.value)} ${trend}`);
  }
  const pib = byId.get("pib_spain");
  if (pib?.value != null) {
    const delta = pib.delta ?? 0;
    push("pib", delta >= 0 ? "good" : "bad", `PIB ${delta >= 0 ? "acelera" : "se enfría"} (${pct(pib.value)})`);
  }
  const ipc = byId.get("ipc_general");
  if (ipc?.value != null) {
    const tone = ipc.value <= 2 ? "good" : ipc.value > 3 ? "bad" : "flat";
    push("ipc", tone, `Inflación en ${pct(ipc.value)} ${ipc.value <= 2 ? "(objetivo BCE)" : ""}`);
  }
  const conf = byId.get("confianza_consumidor_spain");
  if (conf?.value != null) {
    const delta = conf.delta ?? 0;
    push("confianza", delta >= 0 ? "good" : "bad", `Confianza del consumidor ${delta >= 0 ? "mejora" : "empeora"}`);
  }
  return items;
}

const TONE_DOT: Record<string, string> = {
  good: "bg-emerald-400",
  bad: "bg-red-400",
  flat: "bg-amber-300",
};

// ── Simulador de hipoteca sobre Euríbor (Fase 1) ─────────────────────
function frenchQuota(capital: number, annualRatePct: number, months: number): number {
  if (months <= 0 || capital <= 0) return 0;
  const r = annualRatePct / 100 / 12;
  if (r === 0) return capital / months;
  return (capital * r) / (1 - Math.pow(1 + r, -months));
}

function MortgageSimulator({ euribor }: { euribor: PersonalEconomyMI["euribor"] }) {
  const [capital, setCapital] = useState(() => Number(localStorage.getItem("economy.mortgage.capital")) || 120000);
  const [years, setYears] = useState(() => Number(localStorage.getItem("economy.mortgage.years")) || 25);
  const [spread, setSpread] = useState(() => Number(localStorage.getItem("economy.mortgage.spread")) || 1.0);

  const save = (key: string, value: number) => localStorage.setItem(`economy.mortgage.${key}`, String(value));

  const result = useMemo(() => {
    if (euribor.value === null) return null;
    const months = years * 12;
    const now = frenchQuota(capital, euribor.value + spread, months);
    const before = euribor.year_ago !== null ? frenchQuota(capital, euribor.year_ago + spread, months) : null;
    return { now, delta: before !== null ? now - before : null };
  }, [capital, years, spread, euribor]);

  const field = "w-full rounded-lg border border-hairline-dark bg-[var(--bg-interactive)] px-2 py-1.5 text-sm text-on-dark";
  return (
    <div className="premium-card rounded-lg p-5 space-y-3">
      <div className="flex items-center gap-2">
        <Home size={14} className="text-primary-bright" />
        <h3 className="text-caption text-mute uppercase tracking-widest">Tu hipoteca y el Euríbor</h3>
      </div>
      <p className="text-body-sm text-stone">
        Euríbor 12M: <b className="text-on-dark">{pct(euribor.value, 2)}</b>
        {euribor.year_ago !== null && <> · hace un año {pct(euribor.year_ago, 2)}</>}
      </p>
      <div className="grid grid-cols-3 gap-2">
        <label className="text-[11px] text-stone space-y-1">
          <span>Capital pendiente</span>
          <input type="number" className={field} value={capital} min={0}
            onChange={(e) => { const v = Number(e.target.value); setCapital(v); save("capital", v); }} />
        </label>
        <label className="text-[11px] text-stone space-y-1">
          <span>Años restantes</span>
          <input type="number" className={field} value={years} min={1} max={40}
            onChange={(e) => { const v = Number(e.target.value); setYears(v); save("years", v); }} />
        </label>
        <label className="text-[11px] text-stone space-y-1">
          <span>Diferencial (%)</span>
          <input type="number" step="0.1" className={field} value={spread}
            onChange={(e) => { const v = Number(e.target.value); setSpread(v); save("spread", v); }} />
        </label>
      </div>
      {result ? (
        <div className="rounded-lg border border-hairline-dark bg-[var(--bg-interactive)] p-3">
          <p className="text-body-sm text-on-dark">
            Cuota estimada: <b>{formatCurrency(result.now)}</b>/mes
          </p>
          {result.delta !== null && Math.abs(result.delta) >= 0.5 && (
            <p className={`text-caption mt-1 ${result.delta > 0 ? "text-red-300" : "text-emerald-300"}`}>
              {result.delta > 0 ? "+" : ""}{formatCurrency(result.delta)}/mes frente a la revisión de hace un año
            </p>
          )}
          {result.delta !== null && Math.abs(result.delta) < 0.5 && (
            <p className="text-caption text-stone mt-1">Sin cambios relevantes frente a hace un año</p>
          )}
        </div>
      ) : (
        <p className="text-caption text-stone">Sin dato de Euríbor todavía.</p>
      )}
    </div>
  );
}

// ── Inflación personal vs IPC (Fase 1) ───────────────────────────────
function PersonalInflation({ data }: { data: PersonalEconomyMI["personal_inflation"] }) {
  const has = data.user_yoy_pct !== null;
  const worse = has && data.ipc_general !== null && data.user_yoy_pct! > data.ipc_general;
  return (
    <div className="premium-card rounded-lg p-5 space-y-3">
      <div className="flex items-center gap-2">
        <Wallet size={14} className="text-primary-bright" />
        <h3 className="text-caption text-mute uppercase tracking-widest">Tu inflación personal</h3>
      </div>
      {has ? (
        <>
          <div className="flex items-baseline gap-3">
            <span className={`text-2xl font-semibold ${worse ? "text-red-300" : "text-emerald-300"}`}>
              {pct(data.user_yoy_pct)}
            </span>
            <span className="text-caption text-stone">
              tu gasto (12m vs 12m ant.) · IPC {pct(data.ipc_general)} · subyacente {pct(data.ipc_subyacente)}
            </span>
          </div>
          <p className="text-body-sm text-stone">
            {worse
              ? "Tu cesta sube más que la media: revisa las categorías que más crecen."
              : "Tu gasto crece menos que el IPC: mantienes poder adquisitivo."}
          </p>
          <div className="space-y-1.5">
            {data.by_category.slice(0, 5).map((c) => (
              <div key={c.category} className="flex items-center justify-between text-caption">
                <span className="text-stone">{c.category}</span>
                <span className="text-on-dark">
                  {formatCurrency(c.current)}{" "}
                  <span className={c.yoy_pct !== null && c.yoy_pct > 0 ? "text-red-300" : "text-emerald-300"}>
                    {c.yoy_pct !== null ? `${c.yoy_pct > 0 ? "+" : ""}${c.yoy_pct}%` : ""}
                  </span>
                </span>
              </div>
            ))}
          </div>
        </>
      ) : (
        <p className="text-caption text-stone">
          Necesitas al menos 13 meses de movimientos para comparar tu inflación con el IPC.
        </p>
      )}
    </div>
  );
}

// ── Salario real (Fase 2) ────────────────────────────────────────────
function RealSalary({ data }: { data: PersonalEconomyMI["real_salary"] }) {
  const has = data.real_yoy_pct !== null;
  const Icon = has && data.real_yoy_pct! >= 0 ? TrendingUp : TrendingDown;
  return (
    <div className="premium-card rounded-lg p-5 space-y-3">
      <div className="flex items-center gap-2">
        <Landmark size={14} className="text-primary-bright" />
        <h3 className="text-caption text-mute uppercase tracking-widest">Salario real</h3>
      </div>
      {has ? (
        <>
          <div className="flex items-center gap-2">
            <Icon size={18} className={data.real_yoy_pct! >= 0 ? "text-emerald-300" : "text-red-300"} />
            <span className={`text-2xl font-semibold ${data.real_yoy_pct! >= 0 ? "text-emerald-300" : "text-red-300"}`}>
              {data.real_yoy_pct! > 0 ? "+" : ""}{pct(data.real_yoy_pct)}
            </span>
            <span className="text-caption text-stone">poder adquisitivo interanual</span>
          </div>
          <p className="text-body-sm text-stone">
            Nómina {formatCurrency(data.monthly_now ?? 0)}/mes ({data.nominal_yoy_pct! > 0 ? "+" : ""}
            {pct(data.nominal_yoy_pct)} nominal) menos IPC {pct(data.ipc)} ={" "}
            {data.real_yoy_pct! >= 0 ? "ganas" : "pierdes"} poder de compra.
          </p>
        </>
      ) : (
        <p className="text-caption text-stone">
          Sin nóminas suficientes (categoría Salario) en los últimos 15 meses para calcularlo.
        </p>
      )}
    </div>
  );
}

// ── Remuneración del ahorro (Fase 1) ─────────────────────────────────
function SavingsYield({ data }: { data: PersonalEconomyMI["savings"] }) {
  return (
    <div className="premium-card rounded-lg p-5 space-y-3">
      <div className="flex items-center gap-2">
        <PiggyBank size={14} className="text-primary-bright" />
        <h3 className="text-caption text-mute uppercase tracking-widest">Tu liquidez y los tipos</h3>
      </div>
      <p className="text-body-sm text-stone">
        Liquidez en cuentas: <b className="text-on-dark">{formatCurrency(data.idle_liquidity)}</b>
        {data.tipo_bce !== null && <> · tipo BCE {pct(data.tipo_bce, 2)}</>}
      </p>
      {data.potential_monthly !== null && data.potential_monthly >= 1 ? (
        <p className="text-body-sm text-emerald-300">
          Remunerada al tipo BCE rentaría ~{formatCurrency(data.potential_monthly)}/mes
          (cuenta remunerada o Letras del Tesoro).
        </p>
      ) : (
        <p className="text-caption text-stone">
          {data.tipo_bce === null ? "Sin dato del tipo BCE todavía." : "Poca liquidez ociosa que remunerar."}
        </p>
      )}
    </div>
  );
}

// ── Noticias relevantes (Fase 3) ─────────────────────────────────────
function RelevantNews({ items }: { items: PersonalEconomyMI["relevant_news"] }) {
  if (items.length === 0) return null;
  return (
    <div className="premium-card rounded-lg p-5 space-y-3">
      <div className="flex items-center gap-2">
        <Newspaper size={14} className="text-primary-bright" />
        <h3 className="text-caption text-mute uppercase tracking-widest">Noticias que te afectan</h3>
      </div>
      <div className="space-y-2">
        {items.map((n) => (
          <a key={n.id} href={n.url ?? undefined} target="_blank" rel="noreferrer" className="block group">
            <p className="text-body-sm text-on-dark group-hover:text-primary-bright">{n.title}</p>
            <p className="text-caption text-stone">
              {n.source_name}{n.matched.length > 0 && <> · {n.matched.join(", ")}</>}
            </p>
          </a>
        ))}
      </div>
    </div>
  );
}

// ── Sección completa ─────────────────────────────────────────────────
export default function PersonalEconomySection({
  data,
  macroSpain,
}: {
  data: PersonalEconomyMI | null;
  macroSpain: MacroDataPointMI[];
}) {
  if (!data) return null;
  const context = contextItems(macroSpain);
  return (
    <section className="space-y-4">
      <h2 className="text-caption text-mute uppercase tracking-widest">Tu economía</h2>
      {context.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {context.map((c) => (
            <span key={c.id} className="flex items-center gap-2 rounded-lg border border-hairline-dark bg-[var(--bg-interactive)] px-3 py-1.5 text-caption text-on-dark">
              <span className={`h-2 w-2 rounded-full ${TONE_DOT[c.tone]}`} />
              {c.text}
            </span>
          ))}
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <PersonalInflation data={data.personal_inflation} />
        <MortgageSimulator euribor={data.euribor} />
        <RealSalary data={data.real_salary} />
        <SavingsYield data={data.savings} />
        <RelevantNews items={data.relevant_news} />
      </div>
    </section>
  );
}
