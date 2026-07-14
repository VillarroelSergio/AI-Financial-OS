import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Sparkles } from "lucide-react";
import { getCopilotContext } from "@/features/assistant/contextualCopilot";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { PageHeader } from "@/components/ui/Dashboard";
import { getInstrumentHistory } from "@/lib/api/market-intelligence";
import type { HistoryRange, InstrumentHistoryMI } from "@/lib/types/market-intelligence";

const RANGE_LABELS: Record<HistoryRange, string> = {
  "1d": "1d", "5d": "5d", "1m": "1m", "6m": "6m", "1y": "1a", "5y": "5a", max: "Todos",
};
const REGION_LABELS: Record<string, string> = {
  US: "🇺🇸 EE.UU.", ES: "🇪🇸 España", DE: "🇩🇪 Alemania", FR: "🇫🇷 Francia",
  GB: "🇬🇧 Reino Unido", JP: "🇯🇵 Japón", EA: "🇪🇺 Eurozona", GLOBAL: "🌐 Global",
};
const DATE_FMT = new Intl.DateTimeFormat("es-ES", { day: "2-digit", month: "short", year: "2-digit" });

function fmt(v: number | null | undefined, decimals = 2): string {
  if (v == null) return "—";
  return v.toLocaleString("es-ES", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}
const dayLabel = (iso: string) => DATE_FMT.format(new Date(`${iso}T00:00:00`));

function useInstrumentHistory(code: string) {
  const [range, setRange] = useState<HistoryRange>("max");
  const [data, setData] = useState<InstrumentHistoryMI | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    getInstrumentHistory(code, range)
      .then((r) => { if (alive) { setData(r); setError(false); } })
      .catch(() => { if (alive) setError(true); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [code, range]);

  return { range, setRange, data, loading, error };
}

function StatTile({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-hairline-dark bg-[var(--bg-interactive)] px-4 py-3">
      <p className="text-caption text-stone">{label}</p>
      <p className="text-body-sm font-semibold text-on-dark tabular-nums mt-0.5">{value}</p>
    </div>
  );
}

export default function InstrumentDetailPage() {
  const { indicatorCode = "" } = useParams();
  const navigate = useNavigate();
  const { range, setRange, data, loading, error } = useInstrumentHistory(indicatorCode);

  const askAI = () => {
    const name = data?.name ?? indicatorCode.replace(/_/g, " ");
    const prompt = `Analiza el instrumento "${name}" (${indicatorCode}). Usa get_instrument_history para leer su serie EOD y coméntame tendencia, rango 52 semanas y qué vigilar; no inventes cifras.`;
    navigate("/assistant", {
      state: { prompt, context: { ...getCopilotContext("/markets"), instrument_code: indicatorCode } },
    });
  };

  const lastClose = data && data.series.length ? data.series[data.series.length - 1].close : null;
  const firstClose = data && data.series.length ? data.series[0].close : null;
  // El Δ y el color siguen el RANGO seleccionado (primer→último punto visible), no el día:
  // así 3m/6m en verde no se pintan de rojo por un último día negativo.
  const changeAbs = lastClose != null && firstClose != null ? lastClose - firstClose : null;
  const changePct =
    data?.stats.range_change_pct ??
    (changeAbs != null && firstClose ? (changeAbs / firstClose) * 100 : null);
  const positive = (changePct ?? 0) >= 0;
  const currency = data?.currency ?? "";
  const chartColor = positive ? "var(--positive)" : "var(--negative)";

  const chartData = useMemo(
    () => (data?.series ?? []).map((p) => ({ date: p.date, close: p.close })),
    [data]
  );

  const title = data?.name ?? indicatorCode.replace(/_/g, " ");
  const region = data?.region ? (REGION_LABELS[data.region] ?? data.region) : null;

  return (
    <div className="p-8 space-y-6 max-w-[1100px]">
      <Link to="/markets" className="inline-flex items-center gap-1.5 text-caption text-stone hover:text-on-dark transition-colors">
        <ArrowLeft size={14} /> Mercados
      </Link>

      <PageHeader
        eyebrow="Ficha de instrumento"
        title={title}
        description={region ? `${region} · Datos de cierre diario` : "Datos de cierre diario"}
      />

      {loading && <div className="premium-card rounded-lg h-80 animate-pulse" />}

      {!loading && (error || !data || data.series.length === 0) && (
        <div className="premium-card rounded-lg p-10 text-center space-y-3">
          <p className="text-body-sm text-on-dark">Sin histórico local aún</p>
          <p className="text-caption text-stone">
            Aún no hay serie diaria para este instrumento. Ejecuta el backfill para descargarla:
          </p>
          <code className="inline-block rounded bg-[var(--bg-interactive)] px-3 py-1.5 text-caption text-primary-bright">
            python cli.py mi:backfill-history --years=1
          </code>
        </div>
      )}

      {!loading && data && data.series.length > 0 && (
        <>
          {/* Cabecera de valor */}
          <section className="premium-card rounded-lg p-6">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <p className="text-3xl font-semibold text-on-dark tabular-nums">
                  {fmt(lastClose, lastClose != null && lastClose < 10 ? 4 : 2)}
                  <span className="text-body-sm text-stone ml-2">{currency}</span>
                </p>
                {changeAbs != null && (
                  <p className={`text-body-sm font-medium mt-1 ${positive ? "text-accent-teal" : "text-accent-danger"}`}>
                    {positive ? "▲" : "▼"} {fmt(Math.abs(changeAbs))} ({fmt(Math.abs(changePct ?? 0))}%)
                  </p>
                )}
              </div>
              <div className="flex flex-col items-end gap-2">
                <button
                  onClick={askAI}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-primary/15 px-3 py-1.5 text-caption text-primary-bright hover:bg-primary/25 transition-colors"
                >
                  <Sparkles size={14} /> Preguntar a la IA
                </button>
                <div className="text-right text-caption text-stone">
                  <p>Al cierre: {data.last_updated ? dayLabel(data.last_updated) : "—"}</p>
                  <p className="mt-0.5">Calidad {fmt(data.quality_score * 100, 0)}% · {data.provider_id ?? "—"}</p>
                </div>
              </div>
            </div>
          </section>

          {/* Selector de rango — solo rangos que la serie cubre */}
          <div className="flex w-fit gap-1 rounded-lg border border-hairline-dark bg-[var(--bg-interactive)] p-1">
            {data.available_ranges.map((r) => (
              <button
                key={r}
                onClick={() => setRange(r)}
                className={[
                  "rounded-lg px-3.5 py-1.5 text-body-sm transition-colors",
                  range === r
                    ? "bg-primary/20 text-primary-bright shadow-[inset_0_0_0_1px_rgba(91,94,247,.35)]"
                    : "text-stone hover:text-on-dark",
                ].join(" ")}
              >
                {RANGE_LABELS[r] ?? r}
              </button>
            ))}
          </div>

          {/* Gráfico de área */}
          <section className="premium-card rounded-lg p-5">
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={chartData} margin={{ top: 8, right: 8, bottom: 4, left: 4 }}>
                  <defs>
                    <linearGradient id="instrFill" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={chartColor} stopOpacity={0.3} />
                      <stop offset="100%" stopColor={chartColor} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="rgba(255,255,255,0.06)" vertical={false} />
                  <XAxis dataKey="date" tick={{ fill: "#a8adb3", fontSize: 11 }} axisLine={false} tickLine={false} minTickGap={48} tickFormatter={dayLabel} />
                  <YAxis tick={{ fill: "#a8adb3", fontSize: 11 }} axisLine={false} tickLine={false} width={64} domain={["auto", "auto"]} tickFormatter={(v: number) => fmt(v, 0)} />
                  {firstClose != null && (
                    <ReferenceLine y={firstClose} stroke="rgba(255,255,255,0.25)" strokeDasharray="4 4" />
                  )}
                  <Tooltip
                    labelFormatter={(l) => dayLabel(String(l))}
                    formatter={(value) => [`${fmt(Number(value))} ${currency}`, "Cierre"]}
                    contentStyle={{ background: "#16181a", border: "1px solid rgba(255,255,255,0.12)", borderRadius: 8, color: "#fff", fontSize: 12 }}
                  />
                  <Area type="monotone" dataKey="close" stroke={chartColor} strokeWidth={2} fill="url(#instrFill)" isAnimationActive={false} />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </section>

          {/* Panel de estadísticas */}
          <section className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <StatTile label="Cierre anterior" value={fmt(data.stats.previous_close)} />
            <StatTile label="Apertura" value={fmt(data.stats.open)} />
            <StatTile label="Rango del día" value={`${fmt(data.stats.day_low)} – ${fmt(data.stats.day_high)}`} />
            <StatTile label="Rango 52 sem." value={`${fmt(data.stats.week52_low)} – ${fmt(data.stats.week52_high)}`} />
            <StatTile label={`Variación ${RANGE_LABELS[data.range] ?? data.range}`} value={data.stats.range_change_pct != null ? `${fmt(data.stats.range_change_pct)}%` : "—"} />
            <StatTile label="Volumen" value={data.stats.volume != null ? data.stats.volume.toLocaleString("es-ES") : "—"} />
          </section>

          {/* Metadatos de calidad */}
          <section className="premium-card rounded-lg p-5 grid grid-cols-2 sm:grid-cols-4 gap-4 text-body-sm">
            <div><p className="text-caption text-stone">Proveedor</p><p className="text-on-dark">{data.provider_id ?? "—"}</p></div>
            <div><p className="text-caption text-stone">Último dato</p><p className="text-on-dark">{data.last_updated ? dayLabel(data.last_updated) : "—"}</p></div>
            <div><p className="text-caption text-stone">Observaciones</p><p className="text-on-dark tabular-nums">{data.series.length}</p></div>
            <div><p className="text-caption text-stone">Granularidad</p><p className="text-on-dark">Cierre diario (EOD)</p></div>
          </section>
        </>
      )}
    </div>
  );
}
