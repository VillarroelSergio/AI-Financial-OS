// apps/desktop/src/features/economy/components/ImpactCard.tsx
import type { ImpactComparative } from "@/lib/types/market-intelligence";

const COLOR: Record<string, string> = {
  positive: "text-accent-success",
  neutral: "text-stone",
  negative: "text-accent-danger",
  warning: "text-amber-400",
};

const BADGE: Record<string, string> = {
  positive: "bg-accent-success/10 text-accent-success border-accent-success/20",
  neutral: "bg-stone/10 text-stone border-stone/20",
  negative: "bg-accent-danger/10 text-accent-danger border-accent-danger/20",
  warning: "bg-amber-400/10 text-amber-400 border-amber-400/20",
};

const ICON: Record<string, string> = {
  positive: "✅",
  neutral: "➖",
  negative: "⚠️",
  warning: "⚠️",
};

interface Props {
  item: ImpactComparative;
}

export default function ImpactCard({ item }: Props) {
  return (
    <div className="rounded-xl border border-hairline-dark bg-surface-elevated p-4 flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <span className="text-body-sm text-on-dark font-medium">{item.title}</span>
        <span className={`text-caption border rounded px-2 py-0.5 flex-shrink-0 flex items-center gap-1 ${BADGE[item.signal]}`}>
          {ICON[item.signal]}
          <span className="capitalize">{item.signal}</span>
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

      <p className={`text-caption leading-relaxed ${COLOR[item.signal]}`}>{item.signal_text}</p>
      <p className="text-caption text-stone leading-relaxed">{item.description}</p>
    </div>
  );
}
