import { motion } from "framer-motion";
import { springPanel } from "./motion";

export interface SegmentOption<T extends string> {
  key: T;
  label: string;
}

/** Control segmentado estilo iOS: thumb blanco (o gris en oscuro) que se desliza sobre una pista recesada. */
export default function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  ariaLabel,
}: {
  options: SegmentOption<T>[];
  value: T;
  onChange: (key: T) => void;
  ariaLabel?: string;
}) {
  return (
    <div role="tablist" aria-label={ariaLabel} className="inline-flex w-fit gap-1 rounded-[10px] bg-[var(--bg-interactive)] p-1">
      {options.map((opt) => {
        const active = opt.key === value;
        return (
          <button
            key={opt.key}
            role="tab"
            aria-selected={active}
            onClick={() => onChange(opt.key)}
            className={`relative rounded-[8px] px-4 py-1.5 text-sm font-medium transition-colors ${
              active ? "text-[var(--text-primary)]" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            }`}
          >
            {active && (
              <motion.span
                layoutId={`seg-${ariaLabel ?? "default"}`}
                transition={springPanel}
                className="absolute inset-0 rounded-[8px] bg-[var(--bg-segment-thumb)] shadow-[var(--shadow-card)]"
              />
            )}
            <span className="relative z-10">{opt.label}</span>
          </button>
        );
      })}
    </div>
  );
}
