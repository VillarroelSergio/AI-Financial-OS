import { TrendingUp, TrendingDown, Minus, AlertTriangle, CircleOff } from "lucide-react";
import type { ImpactComparative } from "@/lib/types/market-intelligence";

const SIGNAL_CONFIG = {
  no_data: {
    label: "Sin datos",
    textColor: "text-mute",
    badgeClass: "bg-[var(--bg-interactive)] text-mute border-white/10",
    Icon: CircleOff,
  },
  positive: {
    label: "Positivo",
    textColor: "text-[var(--economy-accent)]",
    badgeClass: "bg-[var(--economy-accent-soft)] text-[var(--economy-accent)] border-[var(--economy-accent)]/25",
    Icon: TrendingUp,
  },
  neutral: {
    label: "Neutral",
    textColor: "text-stone",
    badgeClass: "bg-stone/10 text-stone border-stone/20",
    Icon: Minus,
  },
  negative: {
    label: "Negativo",
    textColor: "text-[var(--economy-negative)]",
    badgeClass: "bg-[var(--economy-negative-soft)] text-[var(--economy-negative)] border-[var(--economy-negative)]/25",
    Icon: TrendingDown,
  },
  warning: {
    label: "Atención",
    textColor: "text-[var(--economy-negative)]",
    badgeClass: "bg-[var(--economy-negative-soft)] text-[var(--economy-negative)] border-[var(--economy-negative)]/25",
    Icon: AlertTriangle,
  },
} as const;

interface Props {
  item: ImpactComparative;
}

export default function ImpactCard({ item }: Props) {
  const config = SIGNAL_CONFIG[item.signal] ?? SIGNAL_CONFIG.neutral;
  const { Icon } = config;

  return (
    <div
      className={`rounded-xl border border-hairline-dark bg-surface-elevated p-4 flex flex-col gap-3 ${
        item.signal === "no_data" ? "opacity-70" : ""
      }`}
    >
      <div className="flex items-start justify-between gap-3">
        <span className="text-body-sm text-on-dark font-medium">{item.title}</span>
        <span
          className={`text-caption border rounded px-2 py-0.5 flex-shrink-0 flex items-center gap-1.5 ${config.badgeClass}`}
        >
          <Icon size={12} />
          {config.label}
        </span>
      </div>

      <div className="flex items-center gap-4 text-body-sm tabular-nums">
        <div className="flex flex-col gap-0.5">
          <span className="text-caption text-stone">Mercado</span>
          <span className="text-on-dark">{item.market_label}</span>
        </div>
        <div className="w-px h-8 bg-hairline-dark" />
        <div className="flex flex-col gap-0.5">
          <span className="text-caption text-stone">Personal</span>
          <span className="text-on-dark">{item.personal_label}</span>
        </div>
      </div>

      <hr className="border-hairline-dark" />

      <p className={`text-body-sm font-medium leading-relaxed ${config.textColor}`}>
        {item.signal_text}
      </p>
      <p className="text-caption text-stone leading-relaxed">{item.description}</p>
    </div>
  );
}
