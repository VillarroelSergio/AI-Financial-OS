import type { ImpactItem, ImpactInterpretation } from "@/lib/types";

const ICON: Record<ImpactInterpretation, string> = {
  favorable: "✅",
  neutral: "➖",
  adverse: "⚠️",
  no_data: "—",
};

const COLOR: Record<ImpactInterpretation, string> = {
  favorable: "text-accent-success",
  neutral: "text-stone",
  adverse: "text-accent-danger",
  no_data: "text-mute",
};

const BADGE: Record<ImpactInterpretation, string> = {
  favorable: "bg-accent-success/10 text-accent-success border-accent-success/20",
  neutral: "bg-stone/10 text-stone border-stone/20",
  adverse: "bg-accent-danger/10 text-accent-danger border-accent-danger/20",
  no_data: "bg-surface-card text-mute border-hairline-dark",
};

interface Props {
  item: ImpactItem;
}

function fmt(v: number | null): string {
  if (v === null) return "—";
  return `${v.toLocaleString("es-ES", { minimumFractionDigits: 1, maximumFractionDigits: 1 })}%`;
}

export default function ImpactCard({ item }: Props) {
  return (
    <div className="rounded-xl border border-hairline-dark bg-surface-elevated p-4 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <span className="text-body-sm text-on-dark font-medium">{item.title}</span>
        <span
          className={`text-caption border rounded px-2 py-0.5 flex-shrink-0 flex items-center gap-1 ${BADGE[item.interpretation]}`}
        >
          {ICON[item.interpretation]}
          {item.interpretation !== "no_data" && (
            <span className="capitalize">{item.interpretation}</span>
          )}
        </span>
      </div>

      {item.interpretation !== "no_data" && (
        <div className="flex items-center gap-4 text-body-sm tabular-nums">
          <div className="flex flex-col gap-0.5">
            <span className="text-caption text-stone">Macro</span>
            <span className="text-on-dark">{fmt(item.macro_value)}</span>
          </div>
          <div className="w-px h-8 bg-hairline-dark" />
          <div className="flex flex-col gap-0.5">
            <span className="text-caption text-stone">Personal</span>
            <span className="text-on-dark">{fmt(item.personal_value)}</span>
          </div>
          {item.delta !== null && (
            <>
              <div className="w-px h-8 bg-hairline-dark" />
              <div className="flex flex-col gap-0.5">
                <span className="text-caption text-stone">Diferencia</span>
                <span className={COLOR[item.interpretation]}>
                  {item.delta > 0 ? "+" : ""}{fmt(item.delta)}
                </span>
              </div>
            </>
          )}
        </div>
      )}

      <p className="text-caption text-stone leading-relaxed">{item.description}</p>
    </div>
  );
}
