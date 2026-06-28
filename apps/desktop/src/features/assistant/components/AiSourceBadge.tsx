import type { AiSource } from "../types/aiAssistant.types";

interface Props {
  sources: AiSource[];
  quality_score?: number;
}

function qualityColor(score?: number) {
  if (score == null) return "text-stone";
  if (score >= 0.85) return "text-green-400";
  if (score >= 0.65) return "text-yellow-400";
  return "text-red-400";
}

export default function AiSourceBadge({ sources, quality_score }: Props) {
  if (!sources.length) return null;

  const types = [...new Set(sources.map((s) => s.type))];

  return (
    <div className="flex flex-wrap gap-2 mt-2">
      {types.slice(0, 3).map((type) => (
        <span
          key={type}
          className="text-caption px-2 py-0.5 rounded-full bg-surface-elevated border border-hairline-dark text-stone"
        >
          {type.replace(/_/g, " ")}
        </span>
      ))}
      {quality_score != null && (
        <span className={`text-caption ${qualityColor(quality_score)}`}>
          calidad {Math.round(quality_score * 100)}%
        </span>
      )}
    </div>
  );
}
