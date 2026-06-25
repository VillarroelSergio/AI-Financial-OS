// apps/desktop/src/features/markets/components/LiveIndicator.tsx
interface Props {
  secondsSinceUpdate: number;
}

export default function LiveIndicator({ secondsSinceUpdate }: Props) {
  return (
    <div className="flex items-center gap-2">
      <span className="live-dot inline-block w-1.5 h-1.5 rounded-full bg-accent-teal" />
      <span className="text-caption text-stone">
        En vivo · Actualizado hace {secondsSinceUpdate}s
      </span>
    </div>
  );
}
