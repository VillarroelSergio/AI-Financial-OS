import { useState } from "react";
import { ChevronDown, ChevronRight, Wrench } from "lucide-react";
import type { AiToolCall } from "../types/aiAssistant.types";

interface Props {
  toolCalls: AiToolCall[];
}

function statusColor(status: string) {
  if (status === "ok") return "text-green-400";
  if (status === "not_available") return "text-yellow-400";
  return "text-red-400";
}

export default function AiToolTrace({ toolCalls }: Props) {
  const [expanded, setExpanded] = useState(false);

  if (!toolCalls.length) return null;

  return (
    <div className="mt-2">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="flex items-center gap-1.5 text-caption text-stone hover:text-on-dark transition-colors"
      >
        <Wrench size={12} />
        <span>{toolCalls.length} tool{toolCalls.length > 1 ? "s" : ""} usada{toolCalls.length > 1 ? "s" : ""}</span>
        {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
      </button>
      {expanded && (
        <div className="mt-2 space-y-1.5 pl-3 border-l border-hairline-dark">
          {toolCalls.map((tc, i) => (
            <div key={i} className="text-caption">
              <span className={`font-mono ${statusColor(tc.status)}`}>{tc.name}</span>
              {tc.duration_ms != null && (
                <span className="text-mute ml-2">{tc.duration_ms}ms</span>
              )}
              {tc.status === "error" && tc.result?.error != null && (
                <span className="text-red-400 ml-2">{String(tc.result.error)}</span>
              )}
              {tc.status === "not_available" && (
                <span className="text-yellow-400 ml-2">sin datos</span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
