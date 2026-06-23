// apps/desktop/src/features/markets/components/LiveIndicator.tsx
interface Props {
  secondsSinceUpdate: number;
}

export default function LiveIndicator({ secondsSinceUpdate }: Props) {
  return (
    <div className="flex items-center gap-2">
      <span
        className="inline-block w-1.5 h-1.5 rounded-full bg-accent-teal"
        style={{ animation: "live-pulse 2s ease-in-out infinite" }}
      />
      <span className="text-caption text-stone">
        En vivo · Actualizado hace {secondsSinceUpdate}s
      </span>
    </div>
  );
}
