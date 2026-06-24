// apps/desktop/src/features/markets/components/LiveIndicator.tsx
interface Props {
  secondsSinceUpdate: number;
}

export default function LiveIndicator({ secondsSinceUpdate }: Props) {
  return (
    <div
      className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-hairline-dark bg-surface-elevated"
      role="status"
      aria-label={`En vivo. Actualizado hace ${secondsSinceUpdate} segundos`}
    >
      <span
        className="live-dot inline-block w-2 h-2 rounded-full bg-accent-teal flex-shrink-0"
        aria-hidden="true"
      />
      <span className="text-caption text-accent-teal font-medium">En vivo</span>
      <span className="text-caption text-stone">·</span>
      <span className="text-caption text-stone tabular-nums">
        Actualizado hace {secondsSinceUpdate}s
      </span>
    </div>
  );
}
