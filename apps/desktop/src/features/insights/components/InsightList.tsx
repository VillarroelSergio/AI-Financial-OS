import type { Insight } from "../types/insights.types";
import { InsightCard } from "./InsightCard";

interface InsightListProps {
  insights: Insight[];
  onDismiss?: (id: string) => void;
  onAskAI?: (insight: Insight) => void;
}

export function InsightList({ insights, onDismiss, onAskAI }: InsightListProps) {
  return (
    <div className="space-y-3">
      {insights.map((i) => (
        <InsightCard key={i.id} insight={i} onDismiss={onDismiss} onAskAI={onAskAI} />
      ))}
    </div>
  );
}
