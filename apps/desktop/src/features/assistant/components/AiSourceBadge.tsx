import { useState } from "react";
import { ChevronDown, ChevronRight, Database } from "lucide-react";
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
  const [expanded, setExpanded] = useState(false);

  if (!sources.length) return null;

  const compactSources = sources.filter((source, index, arr) => {
    const key = [source.type, source.provider ?? "", source.id ?? "", source.catalog_item_id ?? "", source.observed_at ?? ""].join("|");
    return arr.findIndex((item) => [item.type, item.provider ?? "", item.id ?? "", item.catalog_item_id ?? "", item.observed_at ?? ""].join("|") === key) === index;
  });
  const scored = compactSources.map((source) => source.quality_score).filter((score): score is number => score != null);
  const displayQuality = quality_score ?? (scored.length ? scored.reduce((sum, score) => sum + score, 0) / scored.length : undefined);
  const types = [...new Set(compactSources.map((s) => s.type))];

  return (
    <div className="mt-2">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="flex flex-wrap items-center gap-2 text-caption text-stone hover:text-on-dark transition-colors"
      >
        <Database size={12} />
        <span>Ver datos usados</span>
        {types.slice(0, 3).map((type) => (
          <span
            key={type}
            className="px-2 py-0.5 rounded-full bg-surface-elevated border border-hairline-dark"
          >
            {type.replace(/_/g, " ")}
          </span>
        ))}
        {displayQuality != null && (
          <span className={qualityColor(displayQuality)}>
            calidad {Math.round(displayQuality * 100)}%
          </span>
        )}
        {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
      </button>
      {expanded && (
        <div className="mt-2 space-y-1.5 pl-3 border-l border-hairline-dark">
          {compactSources.slice(0, 8).map((source, index) => (
            <div key={`${source.type}-${source.id ?? index}`} className="text-caption text-stone">
              <span className="text-on-dark">{source.provider ?? source.type}</span>
              <span className="ml-2">{source.type.replace(/_/g, " ")}</span>
              {source.catalog_item_id && <span className="ml-2">{source.catalog_item_id}</span>}
              {source.observed_at && <span className="ml-2">{source.observed_at}</span>}
              {source.quality_score != null && (
                <span className={`ml-2 ${qualityColor(source.quality_score)}`}>
                  {Math.round(source.quality_score * 100)}%
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
