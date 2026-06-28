// apps/desktop/src/features/markets/components/QualityBadge.tsx
interface QualityBadgeProps {
  score: number;
  generatedAt: string;
}

export default function QualityBadge({ score, generatedAt }: QualityBadgeProps) {
  const label = score >= 0.8 ? "Alta calidad" : score >= 0.5 ? "Calidad media" : "Datos limitados";
  const color =
    score >= 0.8
      ? "text-accent-success bg-accent-success/10 border-accent-success/20"
      : score >= 0.5
      ? "text-amber-400 bg-amber-400/10 border-amber-400/20"
      : "text-accent-danger bg-accent-danger/10 border-accent-danger/20";

  const formatted = new Date(generatedAt).toLocaleString("es-ES", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className={`flex items-center gap-1.5 border rounded px-2.5 py-1 text-caption ${color}`}>
      <span aria-hidden="true">●</span>
      <span>{label}</span>
      <span className="text-mute border-l border-current/20 pl-1.5 ml-0.5">{formatted}</span>
    </div>
  );
}
